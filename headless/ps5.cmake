# SPDX-License-Identifier: GPL-3.0-or-later
include("${CMAKE_CURRENT_LIST_DIR}/../tools/ps5.cmake")
# The native toolchain has one shipping configuration. Host checks do not
# load this toolchain and must leave PS5_NATIVE undefined at C++ level.
set(PS5_NATIVE 1 CACHE BOOL "Encore PS5 native platform")
if(NOT PS5_NATIVE)
    message(FATAL_ERROR "The PS5 toolchain requires PS5_NATIVE")
endif()
set(CMAKE_FIND_ROOT_PATH "${sdk}/target" "$ENV{EDEN_NATIVE_C_DEPS}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(CMAKE_C_FLAGS_INIT "${CMAKE_C_FLAGS_INIT} -ffunction-sections -fdata-sections")
set(CMAKE_CXX_FLAGS_INIT "${CMAKE_CXX_FLAGS_INIT} -ffunction-sections -fdata-sections -D_LIBCPP_ENABLE_EXPERIMENTAL=1")
set(CMAKE_CXX_LINK_EXECUTABLE "bash ${CMAKE_CURRENT_LIST_DIR}/../tools/link-headless-native.sh <TARGET> <LINK_FLAGS> <OBJECTS> <LINK_LIBRARIES>")
