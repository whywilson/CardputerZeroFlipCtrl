#pragma once
#include <cstdint>
#include <algorithm>
// Centre-aligned bilinear sampling avoids uneven nearest-neighbour pixel widths.
enum class ViewMode { Native, Fit, Stretch };
inline int view_width(ViewMode mode) { return mode==ViewMode::Native?256:mode==ViewMode::Fit?302:320; }
inline int view_height(ViewMode mode) { return mode==ViewMode::Native?144:170; }
inline ViewMode next_view_mode(ViewMode mode) { return static_cast<ViewMode>((static_cast<int>(mode)+1)%3); }
inline void render_screen(const uint8_t* src, uint16_t* dst, ViewMode mode) {
    const int width=view_width(mode), height=view_height(mode);
    const bool native=mode==ViewMode::Native;
    for(int y=0;y<height;y++) for(int x=0;x<width;x++) {
        unsigned v;
        if(native) v=src[y*256+x];
        else {
            const int sx=std::max(0,std::min(255*256,((2*x+1)*256*256/(2*width))-128));
            const int sy=std::max(0,std::min(143*256,((2*y+1)*144*256/(2*height))-128));
            const int x0=sx/256,y0=sy/256,x1=std::min(x0+1,255),y1=std::min(y0+1,143);
            const unsigned fx=sx%256,fy=sy%256;
            const unsigned top=src[y0*256+x0]*(256-fx)+src[y0*256+x1]*fx;
            const unsigned bottom=src[y1*256+x0]*(256-fx)+src[y1*256+x1]*fx;
            v=(top*(256-fy)+bottom*fy+32768)/65536;
        }
        dst[y*width+x]=((v>>3)<<11)|(((v*130/255)>>2)<<5);
    }
}
