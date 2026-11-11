#include "lvgl/lvgl.h"
#include "scaler.hpp"
#include "key_guide_pixels.hpp"
#include "connection_ui.hpp"
#include <linux/input.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <sys/file.h>
#include <sys/prctl.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <map>
#include <sstream>

static volatile sig_atomic_t running = 1;
static void stop(int) { running = 0; }
static uint64_t ms() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}

extern "C" { void __libc_csu_init(){} void __libc_csu_fini(){} }

int main(int argc, char** argv) {
    signal(SIGINT, stop);
    signal(SIGTERM, stop);

    int lock = open("/tmp/M5CardputerZero-APPLaunch_fcntl.lock", O_CREAT|O_RDWR|O_CLOEXEC, 0666);
    struct flock fl{};
    fl.l_type = F_WRLCK;
    fl.l_whence = SEEK_SET;
    if (lock < 0 || fcntl(lock, F_SETLK, &fl) < 0) return 1;
    ftruncate(lock, 0);
    dprintf(lock, "%d\n", getpid());

    std::string path = "/tmp/flipper-remote-" + std::to_string(getpid());
    int net = socket(AF_UNIX, SOCK_DGRAM|SOCK_NONBLOCK|SOCK_CLOEXEC, 0);
    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    strcpy(addr.sun_path, path.c_str());
    if (bind(net, (sockaddr*)&addr, sizeof(addr)) < 0) return 2;

    pid_t child = fork();
    if (child == 0) {
        prctl(PR_SET_PDEATHSIG, SIGTERM);
        if (getppid() == 1) _exit(1);
        execlp("python3", "python3", argc > 1 ? argv[1] : "bridge.py",
               path.c_str(), argc > 2 ? argv[2] : "192.168.50.2", nullptr);
        _exit(127);
    }

    sockaddr_un dest{};
    dest.sun_family = AF_UNIX;
    strcpy(dest.sun_path, (path + ".net").c_str());

    auto send = [&](const std::string& key, bool down) {
        std::string data = "{\"key\":\"" + key + "\",\"down\":" + (down ? "true" : "false") + "}";
        sendto(net, data.data(), data.size(), 0, (sockaddr*)&dest, sizeof(dest));
    };

    lv_init();
    std::string fb;
    const char* env = getenv("LV_LINUX_FBDEV_DEVICE");
    if (env) fb = env;
    if (fb.empty()) {
        FILE* f = fopen("/proc/fb", "r");
        char line[256];
        int n;
        while (f && fgets(line, sizeof(line), f)) {
            if ((strstr(line, "fb_st7789v") || strstr(line, "panel-mipi-dbid")) &&
                sscanf(line, "%d", &n) == 1) {
                fb = "/dev/fb" + std::to_string(n);
                break;
            }
        }
        if (f) fclose(f);
    }
    if (fb.empty()) {
        kill(child, SIGTERM);
        waitpid(child, nullptr, 0);
        unlink(path.c_str());
        return 3;
    }

    auto* display = lv_linux_fbdev_create();
    lv_linux_fbdev_set_file(display, fb.c_str());

    auto* root = lv_screen_active();
    lv_obj_set_style_bg_color(root, lv_color_hex(0x101318), 0);
    lv_obj_remove_flag(root, LV_OBJ_FLAG_SCROLLABLE);

    static uint16_t pixels[320 * 170];
    static lv_image_dsc_t image{};
    image.header.magic = LV_IMAGE_HEADER_MAGIC;
    image.header.cf = LV_COLOR_FORMAT_RGB565;
    image.header.w = 302;
    image.header.h = 170;
    image.header.stride = 604;
    image.data_size = sizeof(pixels);
    image.data = (uint8_t*)pixels;

    auto* view = lv_image_create(root);
    lv_image_set_src(view, &image);
    lv_obj_set_pos(view, 9, 0);
    lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN); // Hidden until valid frames arrive

    ConnectionUI conn_ui;
    conn_ui.init(root);

    static uint16_t help_pixels[320 * 170];
    render_key_guide(help_pixels);
    static lv_image_dsc_t help_image{};
    help_image.header.magic = LV_IMAGE_HEADER_MAGIC;
    help_image.header.cf = LV_COLOR_FORMAT_RGB565;
    help_image.header.w = 320;
    help_image.header.h = 170;
    help_image.header.stride = 640;
    help_image.data_size = sizeof(help_pixels);
    help_image.data = reinterpret_cast<const uint8_t*>(help_pixels);
    auto* help = lv_image_create(root);
    lv_image_set_src(help, &help_image);
    lv_obj_set_pos(help, 0, 0);
    lv_obj_add_flag(help, LV_OBJ_FLAG_HIDDEN);

    int keyboard = open(getenv("LV_LINUX_KEYBOARD_DEVICE") ?
                        getenv("LV_LINUX_KEYBOARD_DEVICE") :
                        "/dev/input/by-path/platform-3f804000.i2c-event",
                        O_RDONLY | O_NONBLOCK);

    std::map<int, std::string> keys = {
        {KEY_4, "esc"}, {KEY_5, "view"}, {KEY_6, "power"}, {KEY_7, "edit"}, {KEY_8, "run"},
        {KEY_I, "up"}, {KEY_J, "left"}, {KEY_K, "down"}, {KEY_L, "right"},
        {KEY_UP, "up"}, {KEY_DOWN, "down"}, {KEY_LEFT, "left"}, {KEY_RIGHT, "right"},
        {KEY_ENTER, "ok"}, {KEY_BACKSPACE, "back"}, {KEY_TAB, "appsw"},
        {KEY_F, "up"}, {KEY_X, "down"}, {KEY_Z, "left"}, {KEY_C, "right"},
        {KEY_V, "edit"}, {KEY_B, "run"}, {KEY_A, "ptt"}
    };

    std::map<int, std::string> held;
    uint64_t escape = 0, last = ms();
    bool showhelp = false;
    bool is_live = false;
    bool automatic_prompt = false;
    std::string last_title = "CONNECTING...";

    unsigned char packet[36865];
    static uint8_t grey[256 * 144];
    const ViewMode v_mode = ViewMode::Stretch;
    bool have_frame = false;

    auto redraw = [&]() {
        image.header.w = view_width(v_mode);
        image.header.h = view_height(v_mode);
        image.header.stride = image.header.w * 2;
        image.data_size = image.header.stride * image.header.h;
        render_screen(grey, pixels, v_mode);
        lv_image_set_src(view, &image);
        lv_obj_set_pos(view, (320 - image.header.w) / 2, (170 - image.header.h) / 2);
        lv_obj_invalidate(root);
    };

    while (running) {
        input_event e{};
        while (keyboard >= 0 && read(keyboard, &e, sizeof(e)) == sizeof(e)) {
            if (e.type != EV_KEY || e.value == 2) continue;

            // Esc key handling (hold for 900ms exits safely)
            if (e.code == KEY_ESC) {
                if (e.value) {
                    escape = ms();
                } else if (escape) {
                    uint64_t dur = ms() - escape;
                    escape = 0;
                    if (dur < 900) {
                        if (showhelp) {
                            showhelp = false;
                            lv_obj_add_flag(help, LV_OBJ_FLAG_HIDDEN);
                        } else if (conn_ui.settings_open) {
                            // Cancel settings safely without sending back
                            conn_ui.close_settings();
                            if (have_frame && is_live) {
                                lv_obj_remove_flag(view, LV_OBJ_FLAG_HIDDEN);
                            } else {
                                conn_ui.show_center_status(last_title, conn_ui.status_msg);
                            }
                        } else {
                            send("back", true);
                            send("back", false);
                        }
                    }
                }
                continue;
            }

            // The full-screen guide is available even while connection settings are open.
            if (e.code == KEY_H) {
                if (e.value) {
                    for (auto& k : held) send(k.second, false);
                    held.clear();
                    showhelp = !showhelp;
                    if (showhelp) {
                        lv_obj_move_foreground(help);
                        lv_obj_remove_flag(help, LV_OBJ_FLAG_HIDDEN);
                    } else {
                        lv_obj_add_flag(help, LV_OBJ_FLAG_HIDDEN);
                    }
                }
                continue;
            }
            if (showhelp) continue;

            // 'W' key toggles Connection Settings before and after connection
            if (e.code == KEY_W && e.value) {
                automatic_prompt = false;
                if (conn_ui.settings_open) {
                    conn_ui.close_settings();
                    if (have_frame && is_live) {
                        lv_obj_remove_flag(view, LV_OBJ_FLAG_HIDDEN);
                    } else {
                        conn_ui.show_center_status(last_title, conn_ui.status_msg);
                    }
                } else {
                    for (auto& k : held) send(k.second, false);
                    held.clear();
                    if (conn_ui.typed_ip.empty() && !conn_ui.saved_wifi_host.empty()) {
                        conn_ui.typed_ip = conn_ui.saved_wifi_host;
                    }
                    lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN);
                    conn_ui.open_settings();
                }
                continue;
            }

            // Local navigation inside Connection Settings
            if (conn_ui.settings_open) {
                if (e.value) {
                    automatic_prompt = false;
                    if (e.code == KEY_TAB || e.code == KEY_LEFT || e.code == KEY_RIGHT) {
                        conn_ui.cycle_mode();
                    } else if (e.code == KEY_ENTER || e.code == KEY_KPENTER) {
                        std::string host = conn_ui.get_connect_host();
                        if ((conn_ui.mode == MODE_WIFI || !host.empty()) && !is_valid_ipv4(host)) {
                            conn_ui.set_error("Invalid IP address");
                        } else {
                            conn_ui.saved_wifi_host = conn_ui.typed_ip;
                            std::string json_cmd = "{\"action\":\"connect\",\"mode\":\"" +
                                                   std::string(conn_ui.get_mode_str()) +
                                                   "\",\"host\":\"" + host + "\"}";
                            sendto(net, json_cmd.data(), json_cmd.size(), 0, (sockaddr*)&dest, sizeof(dest));
                            conn_ui.close_settings();
                            last_title = "CONNECTING...";
                            std::string sub = (conn_ui.mode == MODE_AUTO) ?
                                "Connecting auto (wired -> " + host + ")..." :
                                "Connecting via WiFi (" + host + ")...";
                            conn_ui.set_status(sub);
                            conn_ui.show_center_status(last_title, sub);
                        }
                    } else if (e.code == KEY_BACKSPACE) {
                        conn_ui.backspace();
                    } else if (e.code == KEY_DELETE) {
                        conn_ui.typed_ip.clear();
                        conn_ui.error_msg.clear();
                        conn_ui.update_panel_view();
                    } else if (e.code == KEY_DOT || e.code == KEY_KPDOT || e.code == KEY_HIRAGANA) {
                        // TCA8418's device keymap uses code 91 for the physical period key.
                        if (conn_ui.typed_ip.size() < 15 && !conn_ui.typed_ip.empty() && conn_ui.typed_ip.back() != '.') {
                            conn_ui.add_char('.');
                        }
                    } else if (e.code >= KEY_1 && e.code <= KEY_9) {
                        conn_ui.add_char('1' + (e.code - KEY_1));
                    } else if (e.code == KEY_0) {
                        conn_ui.add_char('0');
                    } else if (e.code >= KEY_KP1 && e.code <= KEY_KP9) {
                        conn_ui.add_char('1' + (e.code - KEY_KP1));
                    } else if (e.code == KEY_KP0) {
                        conn_ui.add_char('0');
                    }
                }
                continue;
            }

            auto k = keys.find(e.code);
            if (k != keys.end()) {
                if (!e.value && held.count(e.code)) {
                    send(k->second, false);
                    held.erase(e.code);
                } else if (e.value && !showhelp) {
                    send(k->second, true);
                    held[e.code] = k->second;
                }
            }
        }

        // Hold Esc exits
        if (escape && ms() - escape >= 900) running = 0;

        // Process incoming bridge packets
        ssize_t size;
        while ((size = recv(net, packet, sizeof(packet), 0)) > 0) {
            last = ms();
            if (packet[0] == 'F' && size == 36865) {
                memcpy(grey, packet + 1, sizeof(grey));
                have_frame = true;
                is_live = true;
                if (automatic_prompt) {
                    automatic_prompt = false;
                    conn_ui.close_settings();
                }
                redraw();
                lv_image_set_src(view, &image);
                lv_obj_invalidate(view);
                conn_ui.hide_center_status();
                if (!conn_ui.settings_open) {
                    lv_obj_remove_flag(view, LV_OBJ_FLAG_HIDDEN);
                }
            } else if (packet[0] == 'S') {
                packet[size < 36865 ? size : 36864] = 0;
                const char* s_text = (const char*)packet + 1;
                if (strncmp(s_text, "LIVE", 4) == 0) {
                    conn_ui.set_status(s_text);
                    is_live = true;
                    conn_ui.hide_center_status();
                    if (!conn_ui.settings_open && have_frame) {
                        lv_obj_remove_flag(view, LV_OBJ_FLAG_HIDDEN);
                    }
                } else {
                    is_live = false;
                    lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN);
                    std::string raw_s(s_text);
                    std::string title = "NO SIGNAL";
                    std::string sub = raw_s;
                    size_t nl = raw_s.find('\n');
                    if (nl != std::string::npos) {
                        title = raw_s.substr(0, nl);
                        sub = raw_s.substr(nl + 1);
                    } else if (raw_s.find("Connecting") != std::string::npos) {
                        title = "CONNECTING...";
                    }
                    last_title = title;
                    conn_ui.set_status(sub);
                    if (!conn_ui.settings_open) {
                        conn_ui.show_center_status(title, sub);
                    }
                }
            } else if (packet[0] == 'R') {
                // Bridge signals no wired link found: open settings panel
                is_live = false;
                automatic_prompt = true;
                lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN);
                conn_ui.open_settings();
            } else if (packet[0] == 'C') {
                // Bridge startup / state packet: mode\nactive_host\nsaved_wifi_host
                std::string c_data((char*)packet + 1, size > 1 ? size - 1 : 0);
                std::stringstream ss(c_data);
                std::string m, a_host, s_wifi;
                if (std::getline(ss, m)) {
                    while (!m.empty() && (m.back() == '\r' || m.back() == ' ')) m.pop_back();
                    if (m == "auto") conn_ui.mode = MODE_AUTO;
                    else if (m == "wired") conn_ui.mode = MODE_AUTO; // Legacy transport state.
                    else if (m == "wifi") conn_ui.mode = MODE_WIFI;
                }
                if (std::getline(ss, a_host)) {
                    while (!a_host.empty() && (a_host.back() == '\r' || a_host.back() == ' ')) a_host.pop_back();
                    if (!a_host.empty()) conn_ui.active_host = a_host;
                }
                if (std::getline(ss, s_wifi)) {
                    while (!s_wifi.empty() && (s_wifi.back() == '\r' || s_wifi.back() == ' ')) s_wifi.pop_back();
                    if (!s_wifi.empty()) {
                        conn_ui.saved_wifi_host = s_wifi;
                        if (conn_ui.typed_ip.empty()) {
                            conn_ui.typed_ip = s_wifi;
                        }
                    }
                }
                conn_ui.update_panel_view();
            }
        }

        // Connection heartbeat timeout
        if (ms() - last > 4000) {
            is_live = false;
            lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN);
            last_title = "NO SIGNAL";
            if (!conn_ui.settings_open) {
                conn_ui.set_status("Connection timed out");
                conn_ui.show_center_status(last_title, conn_ui.status_msg);
            }
        }

        // Child process status
        int result;
        if (waitpid(child, &result, WNOHANG) == child) {
            is_live = false;
            lv_obj_add_flag(view, LV_OBJ_FLAG_HIDDEN);
            last_title = "TRANSPORT STOPPED";
            conn_ui.set_status("Bridge exited - hold Esc to exit");
            if (!conn_ui.settings_open) {
                conn_ui.show_center_status(last_title, conn_ui.status_msg);
            }
        }

        lv_timer_handler();
        usleep(5000);
    }

    for (auto& k : held) send(k.second, false);
    usleep(100000);
    kill(child, SIGTERM);
    waitpid(child, nullptr, 0);
    close(keyboard);
    close(net);
    unlink(path.c_str());
    unlink((path + ".net").c_str());
    lv_deinit();
    close(lock);
    return 0;
}
