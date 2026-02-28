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
            
            std::cout << "[DB] Успешное подключение!" << std::endl;
            return con; 
        } catch (sql::SQLException &e) {
            attempts++;
            std::cerr << "Ожидание базы. Попытка " << attempts << "/20" << std::endl;
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
                "SELECT t.id, t.subject, t.body, t.status, t.sentiment, "
                "f.name as facility_name, "
                "c.full_name as contact_name, "
                "cat.name as category_name, "
                "gat.type as device_type "
                "FROM ticket t "
                "LEFT JOIN Facility f ON t.facility_id = f.id "
                "LEFT JOIN Contacts c ON t.contact_id = c.id "
                "LEFT JOIN Categories cat ON t.category_id = cat.id "
                "LEFT JOIN Gas_analyzer_type gat ON cat.id = gat.id"; 

            std::unique_ptr<sql::ResultSet> res_db(stmt->executeQuery(query));
            
            json response_data = json::array();
            while (res_db->next()) {
                json item = {
                    {"id", res_db->getInt("id")},
                    {"subject", res_db->getString("subject")},     
                    {"body", res_db->getString("body")},
                    {"sentiment", res_db->getString("sentiment")}, 
                    {"facility", res_db->getString("facility_name")},
                    {"contact", res_db->getString("contact_name")},
                    {"category", res_db->getString("category_name")},
                    {"device_type", res_db->getString("device_type")}, 
                    {"status", res_db->getString("status")}
                };
                response_data.push_back(item);
            }
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(response_data.dump(), "application/json; charset=utf-8");
            
        } catch (const std::exception &e) {
            res.status = 500;
            res.set_content("{\"error\": \"Database error\"}", "application/json");
        }
    });

    server.Post("/api/v1/predict", [](const httplib::Request& req, httplib::Response& res) {
        res.set_header("Access-Control-Allow-Origin", "*");
        res.set_content("{\"status\":\"success\"}", "application/json");
    });

    std::cout << "Server is starting with port: 8080" << std::endl;
    server.listen("0.0.0.0", 8080);
    return 0;
}
