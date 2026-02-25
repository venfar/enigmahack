cmake_minimum_required(VERSION 3.5)

project(backend LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(HEADER_HTTPLIB "/home/fr1zb3e/backend/include/cpp-httplib")
set(HEADER_JSON "/home/fr1zb3e/backend/include/json/include")

add_executable(backend main.cpp)

target_include_directories(backend PRIVATE "${HEADER_HTTPLIB}")
target_include_directories(backend PRIVATE "${HEADER_JSON}")

include(GNUInstallDirs)
install(TARGETS backend
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
