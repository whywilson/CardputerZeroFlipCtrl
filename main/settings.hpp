#pragma once
#include "scaler.hpp"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>
#include <cerrno>
inline std::string view_mode_path() {
    const char* base=std::getenv("XDG_CONFIG_HOME");
    if(base&&base[0]=='/')return std::string(base)+"/flipctl/view-mode";
    base=std::getenv("HOME");
    if(!base||base[0]!='/'){auto* pw=getpwuid(geteuid());base=pw?pw->pw_dir:nullptr;}
    return base?std::string(base)+"/.config/flipctl/view-mode":std::string();
}
inline ViewMode load_view_mode() {
    const auto path=view_mode_path();FILE* file=fopen(path.c_str(),"r");
    if(!file)return ViewMode::Fit;
    int value=-1;char extra;const int count=fscanf(file,"%d %c",&value,&extra);fclose(file);
    return count==1&&value>=0&&value<=2?static_cast<ViewMode>(value):ViewMode::Fit;
}
inline bool save_view_mode(ViewMode mode) {
    const auto path=view_mode_path();if(path.empty())return false;
    const auto folder=path.substr(0,path.rfind('/'));
    for(size_t i=1;i<=folder.size();i++)if(i==folder.size()||folder[i]=='/') {
        if(mkdir(folder.substr(0,i).c_str(),0700)<0&&errno!=EEXIST)return false;
    }
    std::string temp=path+".XXXXXX";int fd=mkstemp(&temp[0]);if(fd<0)return false;
    char data[3]={static_cast<char>('0'+static_cast<int>(mode)),'\n',0};
    bool ok=write(fd,data,2)==2;
    if(ok)ok=fsync(fd)==0;
    if(close(fd)!=0)ok=false;
    if(ok)ok=rename(temp.c_str(),path.c_str())==0;
    if(!ok)unlink(temp.c_str());return ok;
}
