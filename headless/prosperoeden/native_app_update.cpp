// SPDX-License-Identifier: GPL-3.0-or-later
// Official Eden Encore release -> bounded download -> independent PS5 updater.
// This file never writes to /data/homebrew/PPSA99008 itself.
#include "native_app_update.hpp"
#include "launcher_update_release.hpp"
#include "launcher_update_version.hpp"
#include "../update_check/verified_archive.hpp"
#include "../update_check/self_update_protocol.h"
#include "../storage_paths.h"
#include <array>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fcntl.h>
#include <string>
#include <vector>
#include <string_view>
#include <system_error>
#include <sys/stat.h>
#include <unistd.h>

#ifdef PS5_NATIVE
#include "common/httplib.h"
#include <nlohmann/json.hpp>
#include <openssl/cert.h>
#endif

namespace Eden::EncoreUpdate {
namespace {
bool SafePlan(const NativeInstallPlan& plan) {
    const int installed = ParseRevision(plan.installed_revision, false);
    const int latest = ParseRevision(plan.latest_revision, false);
    if (installed < 0 || latest <= installed || latest > 999 ||
        plan.bytes < (1ull << 20) || plan.bytes > (1ull << 30) ||
        !SafeSha256("sha256:" + plan.sha256)) return false;
    constexpr std::string_view prefix =
        "/niakw/ProsperoEden-Encore/releases/download/";
    if (!plan.package_path.starts_with(prefix)) return false;
    const auto subpath = std::string_view(plan.package_path).substr(prefix.size());
    const auto sep = subpath.find('/');
    if (sep == std::string_view::npos || subpath.find('/', sep + 1) != std::string_view::npos)
        return false;
    const auto tag = subpath.substr(0, sep);
    const auto name = subpath.substr(sep + 1);
    return ParseRevision(tag, true) == latest &&
           SafeAssetName(name, tag) && name == plan.package_name;
}
#ifdef PS5_NATIVE
struct TempArchive {
    std::string path;
    int fd = -1;
    ~TempArchive() {
        if (fd >= 0) (void)close(fd);
        if (!path.empty()) (void)unlink(path.c_str());
    }
};
bool SafeVersion(const std::string& text) {
    if (text.size() != 10 || text[2] != '.' || text[6] != '.') return false;
    for (std::size_t i = 0; i < text.size(); ++i) {
        if (i == 2 || i == 6) continue;
        if (text[i] < '0' || text[i] > '9') return false;
    }
    return true;
}
std::string InstalledContentVersion() {
    constexpr const char* root = "/data/homebrew/PPSA99008/sce_sys/param.json";
    std::error_code ec;
    if (std::filesystem::is_symlink(std::filesystem::symlink_status(root, ec)) ||
        ec || std::filesystem::file_size(root, ec) > 65536 || ec) return {};
    std::FILE* stream = std::fopen(root, "rb");
    if (!stream) return {};
    std::array<char,65537> buffer{};
    const auto n = std::fread(buffer.data(),1,buffer.size(),stream);
    const bool read_good = !std::ferror(stream);
    const bool good = std::fclose(stream) == 0 && read_good;
    if (!good || n == 0 || n == buffer.size()) return {};
    auto json = nlohmann::json::parse(buffer.begin(),buffer.begin()+n,nullptr,false);
    if (json.is_discarded() || !json.is_object() ||
        !json.contains("titleId") || !json["titleId"].is_string() ||
        json["titleId"].get<std::string>() != "PPSA99008" ||
        !json.contains("contentVersion") || !json["contentVersion"].is_string())
        return {};
    auto version = json["contentVersion"].get<std::string>();
    return SafeVersion(version) ? version : std::string{};
}
std::string NewContentVersion(int rev) {
    char result[16]{};
    if (rev < 1 || rev > 999) return {};
    std::snprintf(result,sizeof(result),"01.400.%03d",rev);
    return result;
}
bool CreateTemporaryArchive(TempArchive& temp) {
    // Only the app's data root, never the live homebrew folder. Refuse a
    // symlink at the update directory, even when it happens to exist.
    auto dir = std::filesystem::path(Eden::UserDir()) / "updates";
    std::error_code ec;
    if (!std::filesystem::exists(dir, ec)) {
        if (ec || !std::filesystem::create_directory(dir,ec) || ec) return false;
    }
    const auto stat = std::filesystem::symlink_status(dir,ec);
    if (ec || !std::filesystem::is_directory(stat) ||
        std::filesystem::is_symlink(stat)) return false;
    auto candidate = (dir / ".update-XXXXXX").string();
    std::vector<char> path(candidate.begin(),candidate.end());
    path.push_back(0);
    temp.fd = mkstemp(path.data()); // O_CREAT|O_EXCL prevents symlink use
    if (temp.fd < 0) return false;
    temp.path = path.data();
    (void)fchmod(temp.fd,0600);
    return true;
}
bool WriteFully(int fd, const void* data, std::size_t size) {
    const auto* p=static_cast<const char*>(data);
    while (size) {
        const auto n=write(fd,p,size);
        if (n <= 0) return false;
        p+=n;
        size-=static_cast<std::size_t>(n);
    }
    return true;
}
bool DownloadOfficialArchive(const NativeInstallPlan& plan, TempArchive& temp) {
    if (!CreateTemporaryArchive(temp)) return false;
    VerifiedArchive validator(plan.bytes,plan.sha256);
    if (!validator.Valid()) return false;
    httplib::Client client("https://github.com");
    client.set_follow_location(true);
    client.set_connection_timeout(20);
    client.set_read_timeout(35);
    client.load_ca_cert_store(kCert,sizeof(kCert));
    bool status_ok=false;
    const auto response=client.Get(
        plan.package_path,
        [&status_ok](const httplib::Response& r) {
            status_ok=r.status == 200;
            return status_ok;
        },
        [&](const char* bytes,std::size_t length) {
            // Never write more than the exact bounded release size.
            return validator.Valid() && length <= plan.bytes - validator.Bytes() &&
                   WriteFully(temp.fd,bytes,length) &&
                   validator.Accept(bytes,length);
        });
    return response && status_ok && response->status == 200 &&
           validator.Finish() && fsync(temp.fd) == 0;
}
#endif
} // namespace

bool IsSafeNativeInstallPlan(const NativeInstallPlan& plan) {
    return SafePlan(plan);
}

#ifdef PS5_NATIVE
namespace {
struct NetSockaddrIn {
    std::uint8_t length;
    std::uint8_t family;
    std::uint16_t port;
    std::uint32_t address;
    std::uint16_t virtual_port;
    std::uint8_t zero[6];
};
extern "C" {
    int sceKernelOpen(const char*, int, mode_t);
    int sceKernelClose(int);
    std::int64_t sceKernelRead(int, void*, std::size_t);
    int sceNetConnect(int,const void*,std::uint32_t);
    int sceNetSend(int,const void*,std::size_t,int);
    int sceNetRecv(int,void*,std::size_t,int);
    int sceNetSetsockopt(int,int,int,const void*,std::uint32_t);
    int sceNetSocket(const char*,int,int,int);
    int sceNetSocketClose(int);
}
struct Socket {
    int fd = -1;
    ~Socket() { if (fd >= 0) (void)sceNetSocketClose(fd); }
    bool Send(const void* data, std::size_t n) const {
        const auto* bytes=static_cast<const char*>(data);
        while (n) {
            const auto sent=sceNetSend(fd,bytes,n,0);
            if (sent <= 0) return false;
            bytes+=sent;
            n-=static_cast<std::size_t>(sent);
        }
        return true;
    }
    bool Line(std::string& out) const {
        out.clear();
        for (std::size_t n=0; n<=SELF_UPDATE_LINE; ++n) {
            char c{};
            if (sceNetRecv(fd,&c,1,0) != 1) return false;
            if (c == '\n') return true;
            if (c < 32 || c == 127 || n == SELF_UPDATE_LINE) return false;
            out += c;
        }
        return false;
    }
    bool Text(std::string_view line) const {
        return line.size() < SELF_UPDATE_LINE &&
               Send(line.data(),line.size()) && Send("\n",1);
    }
};
bool ConnectLoader(Socket& socket) {
    socket.fd=sceNetSocket("encore_self_update",2,1,6);
    if (socket.fd < 0) return false;
    // SceNet socket-level options in microseconds, as in elevation.cpp.
    constexpr int level=0xffff;
    constexpr int timeout=180000000;
    for (int option : {0x1105,0x1106,0x1109})
        if (sceNetSetsockopt(socket.fd,level,option,&timeout,sizeof(timeout)) < 0)
            return false;
    constexpr std::uint16_t port=SELF_UPDATE_LOADER_PORT;
    const NetSockaddrIn address{sizeof(NetSockaddrIn),2,
        static_cast<std::uint16_t>((port << 8) | (port >> 8)),
        0x0100007f,0,{0}};
    return sceNetConnect(socket.fd,&address,sizeof(address)) == 0;
}
bool StreamBundledHelper(const Socket& socket) {
    constexpr const char* helper="/app0/self-updater.elf";
    std::error_code error;
    const auto status=std::filesystem::symlink_status(helper,error);
    if (error || std::filesystem::is_symlink(status) ||
        !std::filesystem::is_regular_file(status)) return false;
    const auto size=std::filesystem::file_size(helper,error);
    if (error || size < 4096 || size > (16u << 20)) return false;
    const int fd=sceKernelOpen(helper,O_RDONLY,0);
    if (fd < 0) return false;
    std::array<char,65536> chunk{};
    std::uint64_t total=0;
    bool first=true,ok=true;
    while (total < size) {
        const auto take=std::min<std::size_t>(chunk.size(),size-total);
        const auto n=sceKernelRead(fd,chunk.data(),take);
        if (n <= 0 || static_cast<std::size_t>(n) > take) { ok=false; break; }
        if (first) {
            first=false;
            if (n < 4 || chunk[0] != 0x7f || chunk[1] != 'E' ||
                chunk[2] != 'L' || chunk[3] != 'F') { ok=false; break; }
        }
        if (!socket.Send(chunk.data(),static_cast<std::size_t>(n))) {ok=false;break;}
        total+=static_cast<std::size_t>(n);
    }
    (void)sceKernelClose(fd);
    return ok && total == size;
}
bool SendArchive(const Socket& socket,int fd,std::uint64_t bytes) {
    if (lseek(fd,0,SEEK_SET) != 0) return false;
    std::array<char,65536> chunk{};
    std::uint64_t sent=0;
    while (sent < bytes) {
        const auto take=std::min<std::uint64_t>(chunk.size(),bytes-sent);
        const auto n=read(fd,chunk.data(),static_cast<std::size_t>(take));
        if (n <= 0 || static_cast<std::uint64_t>(n) > take) return false;
        const std::uint32_t length=static_cast<std::uint32_t>(n);
        const unsigned char header[4]{
            static_cast<unsigned char>(length & 255),
            static_cast<unsigned char>((length >> 8) & 255),
            static_cast<unsigned char>((length >> 16) & 255),
            static_cast<unsigned char>((length >> 24) & 255)
        };
        if (!socket.Send(header,4) || !socket.Send(chunk.data(),length))
            return false;
        sent+=length;
    }
    const unsigned char end[4]{};
    return socket.Send(end,4);
}
bool Until(const Socket& socket,std::string_view expected,std::string& message) {
    // Progress during helper's extraction is the only valid extra response.
    // Everything else must match the current protocol stage exactly.
    for (int messages=0; messages<100000; ++messages) {
        if (!socket.Line(message)) return false;
        if (message == expected) return true;
        if (message.starts_with("fail ")) return false;
        if (expected == "staged" && message.starts_with("p ")) continue;
        return false;
    }
    return false;
}
bool HandOff(const NativeInstallPlan& plan,const std::string& installed,
             const std::string& newer,int fd,std::string& message) {
    Socket socket;
    if (!ConnectLoader(socket)) {message="PS5 payload loader unavailable.";return false;}
    if (!StreamBundledHelper(socket)) {
        message="Bundled update helper not available.";
        return false;
    }
    const std::array<std::string,9> fields{
        SELF_UPDATE_MAGIC,"update","PPSA99008",installed,newer,
        std::to_string(plan.bytes),plan.sha256,"Eden Encore",plan.latest_revision};
    for (const auto& field:fields)
        if (!socket.Text(field)) {message="Update helper handshake failed.";return false;}
    if (!Until(socket,"ready",message)) return false;
    if (!SendArchive(socket,fd,plan.bytes)) {
        message="Could not transfer the verified archive.";
        return false;
    }
    if (!Until(socket,"staged",message)) return false;
    // The independent helper has inspected ZIP paths, title, version,
    // installed folder, free space and rollback conditions BEFORE apply.
    if (!socket.Text("apply") || !Until(socket,"applying",message))
        return false;
    message="Update staged; closing Eden Encore to apply.";
    return true;
}
} // namespace
#endif

NativeInstallResult InstallNativeApp(const NativeInstallPlan& plan) {
    if (!IsSafeNativeInstallPlan(plan))
        return {false,"Update release or ZIP metadata was rejected."};
#ifndef PS5_NATIVE
    return {false,"Native PS5 installer is unavailable on this host."};
#else
    const auto installed=InstalledContentVersion();
    const auto newer=NewContentVersion(ParseRevision(plan.latest_revision,false));
    if (installed.empty() || newer.empty() || installed >= newer)
        return {false,"Installed PS5 content version does not match this update."};
    TempArchive temp;
    if (!DownloadOfficialArchive(plan,temp))
        return {false,"Update archive download failed size/SHA256 verification."};
    std::string message;
    const bool applying=HandOff(plan,installed,newer,temp.fd,message);
    return {applying,std::move(message)};
#endif
}
} // namespace Eden::EncoreUpdate
