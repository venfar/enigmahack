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

void log_ticket_to_db(const std::string& subject, const std::string& body, const std::string& sentiment) {
    try {
        sql::mysql::MySQL_Driver *driver;
        std::unique_ptr<sql::Connection> con;
        std::unique_ptr<sql::PreparedStatement> pstmt;
        
        driver = sql::mysql::get_mysql_driver_instance();
        con.reset(driver->connect("tcp://db:3306", "root", "root"));
        con->setSchema("enigma_db");
        
        pstmt.reset(con->prepareStatement(
            "INSERT INTO ticket(subject, body, sentiment, facility_id, contact_id, status) VALUES (?, ?, ?, 1, 1, 'open')"
        ));
        
        pstmt->setString(1, subject);
        pstmt->setString(2, body);
        pstmt->setString(3, sentiment);
        pstmt->execute();
        
        std::cout << "[DB] Ticket saved successfully" << std::endl;
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
            std::string text = input_data.value("text", "No content");
            
            std::cout << "Processing new ticket: " << text << std::endl;
            
            std::string detected_sentiment = "neutral"; 
            log_ticket_to_db("API Request", text, detected_sentiment);
            
            json output_status = {
                {"status", "success"},
                {"sentiment", detected_sentiment},
                {"model-version", "1.0.0-alpha"}
            };
            
            res.set_header("Access-Control-Allow-Origin", "*");
            res.set_content(output_status.dump(), "application/json");
        } catch (const std::exception& e) {
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
                "SELECT t.id, t.subject, t.body, t.status, t.sentiment, f.name as facility_name "
                "FROM ticket t "
                "LEFT JOIN Facility f ON t.facility_id = f.id "
                "ORDER BY t.id DESC LIMIT 20"
            ));
            
            json response_data = json::array();
            
            while (res_db->next()) {
                json item = {
                    {"id", res_db->getInt("id")},
                    {"subject", res_db->getString("subject")},
                    {"body", res_db->getString("body")},
                    {"status", res_db->getString("status")},
                    {"sentiment", res_db->getString("sentiment")},
                    {"facility", res_db->getString("facility_name")}
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
