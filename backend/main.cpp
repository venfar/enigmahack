#include <iostream>
#include <string>
#include <memory>
#include <thread>
#include <chrono>
#include "httplib.h"
#include <nlohmann/json.hpp>
#include <mysql_driver.h>
#include <mysql_connection.h>
#include <cppconn/prepared_statement.h>
#include <cppconn/exception.h>
#include <cppconn/statement.h>

using json = nlohmann::json;

std::unique_ptr<sql::Connection> connect_db() {
    sql::mysql::MySQL_Driver *driver = sql::mysql::get_mysql_driver_instance();
    int attempts = 0;
    
    while (attempts < 20) {
        try {
            std::unique_ptr<sql::Connection> con(driver->connect("tcp://db:3306", "root", "root"));
            con->setSchema("enigma_db");
            
            std::unique_ptr<sql::Statement> stmt(con->createStatement());
            stmt->execute("SET NAMES utf8mb4");
            
            std::cout << "[DB] Connected successfully!" << std::endl;
            return con; 
        } catch (sql::SQLException &e) {
            attempts++;
            std::cerr << "[DB] Connection failed (attempt " << attempts << "/20). Error: " << e.what() << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(3)); 
        }
    }
    return nullptr; 
}

void log_ticket_to_db(const std::string& subject, const std::string& body, const std::string& sentiment, int category_id = 1) {
    try {
        auto con = connect_db(); 
        if (!con) return;

        std::unique_ptr<sql::PreparedStatement> pstmt;
        pstmt.reset(con->prepareStatement(
            "INSERT INTO ticket(subject, body, sentiment, facility_id, contact_id, category_id, status) VALUES (?, ?, ?, 1, 1, ?, 'open')"
        ));
        
        pstmt->setString(1, subject);
        pstmt->setString(2, body);
        pstmt->setString(3, sentiment);
        pstmt->setInt(4, category_id);
        pstmt->execute();
    } catch (sql::SQLException &e) {
        std::cerr << "[DB Insert Error] " << e.what() << std::endl;
    }
}

int main() {
    httplib::Server server;
    server.set_mount_point("/", "./frontend");

    server.Get("/api", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto con = connect_db(); 
            if (!con) {
                res.status = 500;
                res.set_content("{\"error\": \"Database not ready\"}", "application/json");
                return;
            }

            std::unique_ptr<sql::Statement> stmt(con->createStatement());
            
            std::string query = 
                "SELECT t.id, t.subject, t.body, t.status, t.sentiment, "
                "f.name as facility_name, c.name as category_name, gat.type as analyzer_type "
                "FROM ticket t "
                "LEFT JOIN Facility f ON t.facility_id = f.id "
                "LEFT JOIN Categories c ON t.category_id = c.id "
                "LEFT JOIN Gas_analyzer_type gat ON c.id = gat.id "
                "ORDER BY t.id DESC LIMIT 50";

            std::unique_ptr<sql::ResultSet> res_db(stmt->executeQuery(query));
            
            json response_data = json::array();
            while (res_db->next()) {
                json item = {
                    {"id", res_db->getInt("id")},
                    {"subject", res_db->getString("subject")},     
                    {"body", res_db->getString("body")},
                    {"status", res_db->getString("status")},
                    {"sentiment", res_db->getString("sentiment")}, 
                    {"facility", res_db->getString("facility_name")},
                    {"category", res_db->getString("category_name")},
                    {"device_type", res_db->getString("analyzer_type")} 
                };
                response_data.push_back(item);
            }
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(response_data.dump(), "application/json; charset=utf-8");
            
        } catch (const std::exception &e) {
            std::cerr << "[API Error] " << e.what() << std::endl;
            res.status = 500;
            res.set_content("{\"error\": \"Internal server error\"}", "application/json");
        }
    });

    server.Post("/api/v1/predict", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto input_data = json::parse(req.body);
            std::string text = input_data.value("text", "");
            std::string sentiment = input_data.value("sentiment", "neutral");
            int category_id = input_data.value("category_id", 1);
            std::string subject = input_data.value("subject", "Новое обращение");
            
            log_ticket_to_db(subject, text, sentiment, category_id);
            
            json output = {{"status", "success"}, {"message", "Processed"}};
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(output.dump(), "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON\"}", "application/json");
        }
    });

    std::cout << "Backend is running on http://0.0.0.0:8080" << std::endl;
    server.listen("0.0.0.0", 8080);
    
    return 0;
}
