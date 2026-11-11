#pragma once
#include "lvgl/lvgl.h"
#include <string>
#include <vector>
#include <cstdint>

enum ConnectionMode {
    MODE_AUTO = 0,
    MODE_WIFI = 1
};

inline bool is_valid_ipv4(const std::string& ip) {
    if (ip.empty() || ip.size() > 15) return false;
    int count = 0;
    int current = 0;
    bool has_digit = false;
    for (size_t i = 0; i < ip.size(); ++i) {
        char c = ip[i];
        if (c >= '0' && c <= '9') {
            current = current * 10 + (c - '0');
            if (current > 255) return false;
            has_digit = true;
        } else if (c == '.') {
            if (!has_digit || count >= 3) return false;
            count++;
            current = 0;
            has_digit = false;
        } else {
            return false;
        }
    }
    return has_digit && count == 3;
}

class ConnectionUI {
public:
    // Root objects
    lv_obj_t* center_title = nullptr;
    lv_obj_t* center_sub = nullptr;
    lv_obj_t* center_hint = nullptr;

    lv_obj_t* panel = nullptr;
    lv_obj_t* p_title = nullptr;
    lv_obj_t* p_mode = nullptr;
    lv_obj_t* p_ip_caption = nullptr;
    lv_obj_t* p_ip_box = nullptr;
    lv_obj_t* p_ip_label = nullptr;
    lv_obj_t* p_hint = nullptr;
    lv_obj_t* p_action = nullptr;

    // State
    ConnectionMode mode = MODE_AUTO;
    std::string typed_ip;
    std::string saved_wifi_host;
    std::string active_host = "";
    std::string status_msg = "Checking Ethernet (192.168.50.2)...";
    std::string error_msg = "";
    bool settings_open = false;

    void init(lv_obj_t* root) {
        // Centered disconnect / NO SIGNAL screen (montserrat_18)
        center_title = lv_label_create(root);
        lv_obj_set_size(center_title, 320, 24);
        lv_obj_set_pos(center_title, 0, 57);
        lv_obj_set_style_text_font(center_title, &lv_font_montserrat_18, 0);
        lv_obj_set_style_text_color(center_title, lv_color_hex(0xff8200), 0);
        lv_obj_set_style_text_align(center_title, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(center_title, "NO SIGNAL");

        center_sub = lv_label_create(root);
        lv_obj_set_size(center_sub, 300, 40);
        lv_obj_set_pos(center_sub, 10, 87);
        lv_obj_set_style_text_font(center_sub, &lv_font_montserrat_12, 0);
        lv_obj_set_style_text_color(center_sub, lv_color_hex(0x9ea8b5), 0);
        lv_obj_set_style_text_align(center_sub, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(center_sub, status_msg.c_str());

        center_hint = lv_label_create(root);
        lv_obj_set_size(center_hint, 320, 18);
        lv_obj_set_pos(center_hint, 0, 146);
        lv_obj_set_style_text_font(center_hint, &lv_font_montserrat_10, 0);
        lv_obj_set_style_text_color(center_hint, lv_color_hex(0x556070), 0);
        lv_obj_set_style_text_align(center_hint, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(center_hint, "[W] Connection Settings   hold [Esc] Exit");

        // Settings Panel: fits 320x170 screen
        panel = lv_obj_create(root);
        lv_obj_set_pos(panel, 0, 0);
        lv_obj_set_size(panel, 320, 170);
        lv_obj_set_style_bg_color(panel, lv_color_hex(0x101318), 0);
        lv_obj_set_style_bg_opa(panel, LV_OPA_COVER, 0);
        lv_obj_set_style_border_width(panel, 1, 0);
        lv_obj_set_style_border_color(panel, lv_color_hex(0x2d3748), 0);
        lv_obj_set_style_radius(panel, 0, 0);
        lv_obj_set_style_pad_all(panel, 0, 0);
        lv_obj_remove_flag(panel, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(panel, LV_OBJ_FLAG_HIDDEN);

        p_title = lv_label_create(panel);
        lv_obj_set_size(p_title, 320, 20);
        lv_obj_set_pos(p_title, 0, 12);
        lv_obj_set_style_text_font(p_title, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(p_title, lv_color_hex(0xff8200), 0);
        lv_obj_set_style_text_align(p_title, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(p_title, "CONNECT");

        p_mode = lv_label_create(panel);
        lv_obj_set_size(p_mode, 300, 20);
        lv_obj_set_pos(p_mode, 10, 44);
        lv_obj_set_style_text_font(p_mode, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(p_mode, lv_color_hex(0xffffff), 0);
        lv_obj_set_style_text_align(p_mode, LV_TEXT_ALIGN_CENTER, 0);

        p_ip_caption = lv_label_create(panel);
        lv_obj_set_size(p_ip_caption, 300, 15);
        lv_obj_set_pos(p_ip_caption, 10, 76);
        lv_obj_set_style_text_font(p_ip_caption, &lv_font_montserrat_10, 0);
        lv_obj_set_style_text_color(p_ip_caption, lv_color_hex(0x9ea8b5), 0);
        lv_obj_set_style_text_align(p_ip_caption, LV_TEXT_ALIGN_CENTER, 0);

        p_ip_box = lv_obj_create(panel);
        lv_obj_set_pos(p_ip_box, 58, 96);
        lv_obj_set_size(p_ip_box, 204, 27);
        lv_obj_set_style_bg_color(p_ip_box, lv_color_hex(0x1a202c), 0);
        lv_obj_set_style_bg_opa(p_ip_box, LV_OPA_COVER, 0);
        lv_obj_set_style_border_width(p_ip_box, 1, 0);
        lv_obj_set_style_border_color(p_ip_box, lv_color_hex(0xff8200), 0);
        lv_obj_set_style_radius(p_ip_box, 3, 0);
        lv_obj_set_style_pad_all(p_ip_box, 0, 0);
        lv_obj_remove_flag(p_ip_box, LV_OBJ_FLAG_SCROLLABLE);

        p_ip_label = lv_label_create(p_ip_box);
        lv_obj_set_size(p_ip_label, 194, 21);
        lv_obj_set_pos(p_ip_label, 5, 3);
        lv_obj_set_style_text_font(p_ip_label, &lv_font_montserrat_14, 0);
        lv_obj_set_style_text_color(p_ip_label, lv_color_hex(0xffffff), 0);
        lv_obj_set_style_text_align(p_ip_label, LV_TEXT_ALIGN_CENTER, 0);

        p_hint = lv_label_create(panel);
        lv_obj_set_size(p_hint, 300, 14);
        lv_obj_set_pos(p_hint, 10, 128);
        lv_obj_set_style_text_font(p_hint, &lv_font_montserrat_10, 0);
        lv_obj_set_style_text_color(p_hint, lv_color_hex(0x718096), 0);
        lv_obj_set_style_text_align(p_hint, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(p_hint, "Tab / Left / Right: mode    0-9 .: IP");

        // Action hint
        p_action = lv_label_create(panel);
        lv_obj_set_size(p_action, 320, 18);
        lv_obj_set_pos(p_action, 0, 150);
        lv_obj_set_style_text_font(p_action, &lv_font_montserrat_10, 0);
        lv_obj_set_style_text_color(p_action, lv_color_hex(0xffaa44), 0);
        lv_obj_set_style_text_align(p_action, LV_TEXT_ALIGN_CENTER, 0);
        lv_label_set_text(p_action, "Enter: connect   Backspace: erase   Esc: close");

        update_panel_view();
    }

    void show_center_status(const std::string& title, const std::string& sub) {
        if (!settings_open) {
            lv_label_set_text(center_title, title.c_str());
            lv_label_set_text(center_sub, sub.c_str());
            lv_obj_remove_flag(center_title, LV_OBJ_FLAG_HIDDEN);
            lv_obj_remove_flag(center_sub, LV_OBJ_FLAG_HIDDEN);
            lv_obj_remove_flag(center_hint, LV_OBJ_FLAG_HIDDEN);
        }
    }

    void hide_center_status() {
        lv_obj_add_flag(center_title, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_flag(center_sub, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_flag(center_hint, LV_OBJ_FLAG_HIDDEN);
    }

    void open_settings() {
        settings_open = true;
        hide_center_status();
        error_msg = "";
        update_panel_view();
        lv_obj_remove_flag(panel, LV_OBJ_FLAG_HIDDEN);
    }

    void close_settings() {
        settings_open = false;
        error_msg = "";
        lv_obj_add_flag(panel, LV_OBJ_FLAG_HIDDEN);
    }

    void cycle_mode() {
        mode = mode == MODE_WIFI ? MODE_AUTO : MODE_WIFI;
        update_panel_view();
    }

    void add_char(char c) {
        if (typed_ip.size() < 15) {
            typed_ip += c;
            error_msg = "";
            update_panel_view();
        }
    }

    void backspace() {
        if (!typed_ip.empty()) {
            typed_ip.pop_back();
            error_msg = "";
            update_panel_view();
        }
    }

    void set_status(const std::string& text) {
        status_msg = text;
        if (center_sub) lv_label_set_text(center_sub, status_msg.c_str());
    }

    void set_error(const std::string& err) {
        error_msg = err;
        update_panel_view();
    }

    std::string get_connect_host() const {
        return typed_ip;
    }

    const char* get_mode_str() const {
        return mode == MODE_WIFI ? "wifi" : "auto";
    }

    void update_panel_view() {
        if (!p_mode) return;
        lv_label_set_text(p_mode, mode == MODE_WIFI ? "AUTO     [ WiFi ]" : "[ AUTO ]     WiFi");
        lv_label_set_text(p_ip_caption, mode == MODE_WIFI ? "DEVICE IP" : "WIRED FIRST  |  WiFi FALLBACK IP");
        std::string disp = typed_ip.empty() ? "IP address_" : typed_ip + "_";
        lv_label_set_text(p_ip_label, disp.c_str());

        if (!error_msg.empty()) {
            lv_label_set_text(p_hint, error_msg.c_str());
            lv_obj_set_style_text_color(p_hint, lv_color_hex(0xff4444), 0);
        } else {
            lv_label_set_text(p_hint, "Tab / Left / Right: mode    0-9 .: IP");
            lv_obj_set_style_text_color(p_hint, lv_color_hex(0x718096), 0);
        }
    }
};
