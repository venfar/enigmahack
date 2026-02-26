cmake_minimum_required(VERSION 3.5)
project(backend LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(HEADER_HTTPLIB "${CMAKE_SOURCE_DIR}/include/cpp-httplib")
set(HEADER_JSON "${CMAKE_SOURCE_DIR}/include/json/include")

find_package(OpenSSL REQUIRED)
find_library(MYSQL_LIB mysqlcppconn)

add_executable(backend main.cpp)

target_include_directories(backend PRIVATE "${HEADER_HTTPLIB}")
target_include_directories(backend PRIVATE "${HEADER_JSON}")
target_include_directories(backend PRIVATE "${OPENSSL_INCLUDE_DIR}")

target_link_libraries(backend PRIVATE 
    ${MYSQL_LIB} 
    OpenSSL::SSL 
    OpenSSL::Crypto
    pthread
)

include(GNUInstallDirs)
install(TARGETS backend
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
