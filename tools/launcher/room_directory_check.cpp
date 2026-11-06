// SPDX-License-Identifier: GPL-3.0-or-later
// Offline R14 regression: no network connections and no PS5 binaries.
#include "room_directory.hpp"
#include <cassert>
#include <string>
#include <nlohmann/json.hpp>
using Eden::Multiplayer::ParseRoomDirectory;
using nlohmann::json;
static json room(std::string ip = "8.8.8.8", unsigned protocol = 7, unsigned players = 2) {
    json members = json::array();
    for(unsigned i=0;i<players;++i) members.push_back(json::object({{"name","friend"}}));
    return {{"name","Friends"}, {"preferredGameName","Racing"}, {"address",ip},
            {"port",24872}, {"maxPlayers",8}, {"players",members},
            {"hasPassword",true}, {"netVersion",protocol}};
}
static auto parse(const json& rows) {
    return ParseRoomDirectory(json{{"rooms",rows}}.dump(),7);
}
int main() {
    {
        auto result=parse(json::array({room()}));
        assert(result.error.empty() && result.rooms.size()==1 &&
               result.rooms[0].compatible && result.rooms[0].players==2);
    }
    {
        auto other=room("1.1.1.1",6,4);
        other["name"]="Other";
        auto result=parse(json::array({other,room("8.8.8.8",7,2)}));
        assert(result.rooms.size()==2 && result.rooms[0].compatible &&
               !result.rooms[1].compatible);
    }
    for(const auto ip: {"127.0.0.1","10.10.2.3","192.168.1.20",
                        "172.16.3.4","100.64.1.1","169.254.1.1",
                        "224.0.0.1","0.0.0.0","255.255.255.255",
                        "localhost","2001:db8::1"}) {
        auto result=parse(json::array({room(ip)}));
        assert(result.rooms.empty() && result.rejected==1);
    }
    {
        auto v=room();
        v["players"]=json::array();
        for(unsigned i=0;i<9;++i) v["players"].push_back(json::object());
        auto result=parse(json::array({v}));
        assert(result.rooms.empty() && result.rejected==1);
    }
    {
        auto v=room(); v["port"]=0;
        auto result=parse(json::array({v,room()}));
        assert(result.rooms.size()==1 && result.rejected==1);
    }
    {
        auto result=ParseRoomDirectory("{ malformed",7);
        assert(!result.error.empty() && result.rooms.empty());
    }
    {
        auto result=ParseRoomDirectory(std::string(Eden::Multiplayer::MaxDirectoryBytes+1,'X'),7);
        assert(result.rooms.empty() && !result.error.empty());
    }
    {
        auto v=room();v["name"]="Friends\nOther";
        auto result=parse(json::array({v}));
        assert(result.rooms.size()==1 && result.rooms[0].name=="Friends Other");
    }
}
