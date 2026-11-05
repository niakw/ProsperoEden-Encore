#!/usr/bin/env python3
"""R10 offline package plus existing native ModFS discovery contract."""
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import shutil
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location(
    "encore_hd_packer", ROOT/"tools/graphics/package-hd-textures.py")
packer=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packer)
TITLE="0100ABCD00001000"


class HdPackTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root=pathlib.Path(self.work.name)
        self.source=self.root/"source"
        self.source.mkdir()
        self.mods=self.root/"mods"

    def sample(self):
        path=self.source/"assets"/"grass.bntx"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"USER_COMPATIBLE_ROMFS"+bytes(range(64)))
        item=self.source/"textures"/"other.bin"
        item.parent.mkdir()
        item.write_bytes(b"ANOTHER_USER_FILE")
        return path,item

    def test_pack_and_mod_scanner(self):
        grass,other=self.sample()
        result=packer.package(self.source,self.mods,TITLE,"Ground HD")
        self.assertEqual(result.name,"HD Textures - Ground HD")
        self.assertEqual(result.parent.name,TITLE)
        manifest=json.loads((result/"encore-hd-textures.json").read_text())
        self.assertEqual(manifest["title_id"],TITLE)
        self.assertEqual(manifest["source"],"user-supplied")
        self.assertEqual(manifest["file_count"],2)
        self.assertEqual((result/"romfs/assets/grass.bntx").read_bytes(),grass.read_bytes())
        self.assertEqual((result/"romfs/textures/other.bin").read_bytes(),other.read_bytes())
        self.assertEqual(manifest["total_bytes"],grass.stat().st_size+other.stat().st_size)
        for entry in manifest["files"]:
            p=result/"romfs"/entry["path"]
            self.assertEqual(p.stat().st_size,entry["bytes"])
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),entry["sha256"])
        # The existing C++ ModFS scanner must see this as a file-only ROMFS
        # mod, not as an ExeFS patch or a made-up GPU texture format.
        source=r'''
#include "mods.h"
#include <cassert>
#include <cstdint>
#include <string>
int main(int argc,char** argv) {
    assert(argc==2);
    const auto mods=Eden::Mods::List(argv[1],0x0100ABCD00001000ULL);
    assert(mods.size()==1);
    assert(mods[0].name=="HD Textures - Ground HD");
    assert(mods[0].kinds==Eden::Mods::kFiles);
    return 0;
}
'''
        exe=self.root/"check_existing_modfs"
        env=dict(os.environ)
        if platform.system()=="Darwin":
            sdk=pathlib.Path("/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk")
            if sdk.exists(): env["SDKROOT"]=str(sdk)
        compiler=os.environ.get("CXX") or shutil.which("clang++") or shutil.which("g++") or "c++"
        compiled=subprocess.run(
            [compiler,"-std=c++20","-O1","-Wall",
             "-Wextra","-Werror","-I"+str(ROOT/"headless"),
             "-x","c++","-","-o",str(exe)],
            input=source,check=False,text=True,capture_output=True,env=env)
        if compiled.returncode:
            self.fail("Native mod scanner host compile failed: "+compiled.stderr)
        subprocess.run([str(exe),str(self.mods)],check=True)

    def test_no_overwrite_and_unsafe_names(self):
        self.sample()
        first=packer.package(self.source,self.mods,TITLE,"Textures")
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Textures")
        self.assertTrue((first/"romfs/assets/grass.bntx").exists())
        for name in ("../escape","/oops","..","", "x"*49, "hidden\nnew"):
            with self.assertRaises(packer.PackError):
                packer.package(self.source,self.mods,TITLE,name)
        for title in ("", "0000000000000000", "garbage", "0"*17):
            with self.assertRaises(packer.PackError):
                packer.package(self.source,self.mods,title,"X")

    def test_symlinks_and_empty_input_fail(self):
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Empty")
        self.sample()
        (self.source/"symlink").symlink_to(self.root)
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Symlink")
        (self.source/"symlink").unlink()
        (self.source/"filelink").symlink_to(self.source/"assets/grass.bntx")
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"File link")
        self.assertFalse((self.mods/TITLE/"HD Textures - File link").exists())

    def test_budget_and_case_insensitive_title_folder(self):
        self.sample()
        self.mods.mkdir()
        (self.mods/TITLE.lower()).mkdir()
        result=packer.package(self.source,self.mods,TITLE,"Tiny")
        self.assertEqual(result.parent.name,TITLE.lower())
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Another",max_file_mib=0)
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Another",max_total_mib=0)

    def test_mods_root_symlink_refused(self):
        self.sample()
        real=self.root/"real"
        real.mkdir()
        self.mods.symlink_to(real)
        with self.assertRaises(packer.PackError):
            packer.package(self.source,self.mods,TITLE,"Unsafe")
        self.assertEqual(list(real.iterdir()),[])


if __name__=="__main__":
    unittest.main(verbosity=2)
