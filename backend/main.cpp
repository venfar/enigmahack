#include <iostream>
#include "httplib.h"
#include <nlohmann/json.hpp>

int main() {
    httplib::Server server;

    json json_format{"status","ok"};

    server.Get("/health",[&json_format](const httplib::Request& req, httplib::Response& res){
        res.set_content(json_format.dump(),"application/json");
    });

    server.Post("/api/v1/predict",[](const httplib::Request& req, httplib::Response& res){
        try {
            auto input_status = json::parse(req.body);
            std::cout << "There was got connection from Django" << "\n";

            json output_status = {
                {"status","success"},
                {"prediction",nullptr},
                {"model-alpha","1.0.0-alpha"}
            };

            res.set_content(output_status.dump(),"application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON\"}", "application/json");
        }
    });
    std::cout << "Starting port: " << 8080 << std::endl;
    server.listen("0.0.0.0",8080);
    return 0;
}
