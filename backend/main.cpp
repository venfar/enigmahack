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
#include <cppconn/resultset.h>

using json = nlohmann::json;

std::string getSafeString(std::unique_ptr<sql::ResultSet>& res, const std::string& column) {
    return res->isNull(column) ? "" : res->getString(column);
}

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
            std::cerr << "DB Waiting... Attempt " << attempts << "/20" << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(3));
        }
    }
    return nullptr; 
}

int main() {
    httplib::Server server;
    
    server.set_mount_point("/", "./frontend");

    server.Get("/api", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto con = connect_db(); 
            if (!con) throw std::runtime_error("DB Connection failed");

            std::unique_ptr<sql::Statement> stmt(con->createStatement());
            
            std::string query = 
                "SELECT t.id, t.email_id, t.body as question_body, t.status, "
                "s.name as sentiment_label, "            
                "gt.type as device_type, "              
                "f.name as facility_name, "             
                "c.full_name as contact_name, "         
                "t.generated_response as ai_reply "     
                "FROM ticket t "
                "LEFT JOIN Sentiment s ON t.sentiment_id = s.id "
                "LEFT JOIN Gas_analyzer ga ON t.gaz_analyzer_id = ga.id "
                "LEFT JOIN Gas_analyzer_type gt ON ga.type_id = gt.id "
                "LEFT JOIN Facility f ON t.facility_id = f.id "
                "LEFT JOIN Contacts c ON t.contact_id = c.id "
                "ORDER BY t.id DESC"; 

            std::unique_ptr<sql::ResultSet> res_db(stmt->executeQuery(query));
            
            json response_data = json::array();
            while (res_db->next()) {
                json row = {
                    {"id", res_db->getInt("id")},
                    {"email_id", getSafeString(res_db, "email_id")},
                    {"issue", getSafeString(res_db, "question_body")},   
                    {"sentiment", getSafeString(res_db, "sentiment_label")}, 
                    {"device", getSafeString(res_db, "device_type")},    
                    {"object", getSafeString(res_db, "facility_name")},
                    {"fio", getSafeString(res_db, "contact_name")},
                    {"status", getSafeString(res_db, "status")},
                    {"answer", getSafeString(res_db, "ai_reply")}
                };
                response_data.push_back(row);
            }
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(response_data.dump(), "application/json; charset=utf-8");
            
        } catch (const std::exception &e) {
            std::cerr << "Error: " << e.what() << std::endl;
            res.status = 500;
            res.set_content("{\"error\": \"Database error\"}", "application/json");
        }
    });

    std::cout << "Backend server started on http://0.0.0.0:8080" << std::endl;
    server.listen("0.0.0.0", 8080);
    return 0;
}
