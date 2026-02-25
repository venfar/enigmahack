cmake_minimum_required(VERSION 3.5)

project(HttpLibBackend LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(HEADER_FILE "/home/fr1zb3e/cpp-httplib")
set(INCLUDE_DIR "/home/fr1zb3e/json/include")

add_executable(HttpLibBackend main.cpp
    Libraries.h)

target_include_directories(HttpLibBackend PRIVATE "${HEADER_FILE}")
target_include_directories(HttpLibBackend PRIVATE "${INCLUDE_DIR}")

include(GNUInstallDirs)
install(TARGETS HttpLibBackend
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
