#include <iostream>
#include <string>
#include <memory>
#include <thread>
#include <chrono>
#include <vector>
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
    try {
        if (res->isNull(column)) return "";
        return res->getString(column);
    } catch (...) {
        return "";
    }
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
            
            std::cout << "[DB] Успешное подключение к базе данных!" << std::endl;
            return con; 
        } catch (sql::SQLException &e) {
            attempts++;
            std::cerr << "[DB] Ожидание БД... Попытка " << attempts << "/20. Ошибка: " << e.what() << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(3));
        }
    }
    return nullptr; 
}

int main() {
    httplib::Server server;
    
    server.Get("/api", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto con = connect_db(); 
            if (!con) throw std::runtime_error("Не удалось подключиться к БД");

            std::unique_ptr<sql::Statement> stmt(con->createStatement());
            
            std::string query = 
                "SELECT "
                "t.created_at as date, "
                "c.full_name as fio, "
                "f.name as object_name, "
                "c.phone as phone, "
                "c.email as email, "
                "ga.serial_number as serial_numbers, "
                "gt.type as device_type, "
                "s.name as sentiment, "
                "t.generated_response as answer "
                "FROM ticket t "
                "LEFT JOIN Contacts c ON t.contact_id = c.id "
                "LEFT JOIN Facility f ON t.facility_id = f.id "
                "LEFT JOIN Sentiment s ON t.sentiment_id = s.id "
                "LEFT JOIN Gas_analyzer ga ON t.gaz_analyzer_id = ga.id "
                "LEFT JOIN Gas_analyzer_type gt ON ga.type_id = gt.id "
                "ORDER BY t.id DESC"; 

            std::unique_ptr<sql::ResultSet> res_db(stmt->executeQuery(query));
            
            json response_data = json::array();
            while (res_db->next()) {
                response_data.push_back({
                    {"date", getSafeString(res_db, "date")},
                    {"fio", getSafeString(res_db, "fio")},
                    {"object_name", getSafeString(res_db, "object_name")},
                    {"phone", getSafeString(res_db, "phone")},
                    {"email", getSafeString(res_db, "email")},
                    {"serial_numbers", getSafeString(res_db, "serial_numbers")},
                    {"device_type", getSafeString(res_db, "device_type")},
                    {"sentiment", getSafeString(res_db, "sentiment")},
                    {"answer", getSafeString(res_db, "answer")}
                });
            }
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(response_data.dump(), "application/json; charset=utf-8");
            
        } catch (const std::exception &e) {
            std::cerr << "[Error] " << e.what() << std::endl;
            res.status = 500;
            res.set_content("{\"error\": \"Database error\"}", "application/json");
        }
    });

    server.Post("/api/v1/predict", [](const httplib::Request& req, httplib::Response& res) {
        try {
            auto input_status = json::parse(req.body);
            std::cout << "[API] Получен запрос на предикт" << std::endl;

            json output_status = {
                {"status", "success"},
                {"prediction", nullptr},
                {"model-alpha", "1.0.0-alpha"}
            };

            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(output_status.dump(), "application/json");
        } catch (...) {
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON\"}", "application/json");
        }
    });

    server.Get("/health", [](const httplib::Request& req, httplib::Response& res) {
        res.set_header("Access-Control-Allow-Origin", "*");
        res.set_content("{\"status\":\"ok\"}", "application/json");
    });

    std::cout << "Backend запущен на http://0.0.0.0:8080" << std::endl;
    server.listen("0.0.0.0", 8080);
    
    return 0;
}
