#pragma once
#include "core/loader/loader.h"
namespace FileSys {
class RomFSFactory {
public:
    RomFSFactory(Loader::AppLoader& loader, ContentProvider&, Service::FileSystem::FileSystemController&) {
        loader.ReadRomFS(file);
    }
    VirtualFile file;
};
}
