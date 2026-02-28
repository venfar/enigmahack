#include <iostream>
#include <string>
#include <memory>
#include "httplib.h"
#include <nlohmann/json.hpp>
#include <mysql_driver.h>
#include <mysql_connection.h>
#include <cppconn/prepared_statement.h>
#include <cppconn/exception.h>

using json = nlohmann::json;

void log_to_mysql(const std::string& request_body, const std::string& status_msg) {
    try {
        sql::mysql::MySQL_Driver *driver;
        std::unique_ptr<sql::Connection> con;
        std::unique_ptr<sql::PreparedStatement> pstmt;
        
        driver = sql::mysql::get_mysql_driver_instance();
        
        con.reset(driver->connect("tcp://db:3306", "root", "root"));
        con->setSchema("enigma_db");
        
        pstmt.reset(con->prepareStatement(
            "INSERT INTO request_history(user_id, request_text, status) VALUES (?, ?, ?)"
        ));
        
        pstmt->setInt(1, 2); 
        pstmt->setString(2, request_body);
        pstmt->setString(3, status_msg);
        pstmt->execute();
        
        std::cout << "[DB] Log saved successfully" << std::endl;
    } catch (sql::SQLException &e) {
        std::cerr << "[DB Insert Error] " << e.what() << " (Code: " << e.getErrorCode() << ")" << std::endl;
    }
}

int main() {
    httplib::Server server;
    
    server.set_mount_point("/", "./frontend");
    
    server.Get("/health", [](const httplib::Request& req, httplib::Response& res) {
        json health = {{"status", "ok"}};
        res.set_content(health.dump(), "application/json");
    });
    
    server.Post("/api/v1/predict", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto input_data = json::parse(req.body);
            std::cout << "Received predict request" << std::endl;
            
            log_to_mysql(req.body, "success");
            
            json output_status = {
                {"status", "success"},
                {"prediction", "some_result"},
                {"model-alpha", "1.0.0-alpha"}
            };
            
            res.set_content(output_status.dump(), "application/json");
        } catch (const std::exception& e) {
            log_to_mysql(req.body, "error");
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON\"}", "application/json");
        }
    });
    
    server.Get("/api", [](const httplib::Request& req, httplib::Response& res) {
        try {
            sql::mysql::MySQL_Driver *driver = sql::mysql::get_mysql_driver_instance();
            std::unique_ptr<sql::Connection> con(driver->connect("tcp://db:3306", "root", "root"));
            con->setSchema("enigma_db");

            std::unique_ptr<sql::Statement> stmt(con->createStatement());

            std::unique_ptr<sql::ResultSet> res_db(stmt->executeQuery(
                "SELECT id, request_text, status FROM request_history ORDER BY id DESC LIMIT 10"
            ));
            
            json response_data = json::array();
            
            while (res_db->next()) {
                json item = {
                    {"id", res_db->getInt("id")},
                    {"text", res_db->getString("request_text")},
                    {"status", res_db->getString("status")}
                };
                response_data.push_back(item);
            }
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(response_data.dump(), "application/json");
            
        } catch (sql::SQLException &e) {
            std::cerr << "[API DB Error] " << e.what() << std::endl;
            res.status = 500;
            res.set_content("{\"error\": \"Database connection error\"}", "application/json");
        }
    });

    std::cout << "Server is starting at http://0.0.0.0:8080" << std::endl;
    server.listen("0.0.0.0", 8080);
    
    return 0;
}
