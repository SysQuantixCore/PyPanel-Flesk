"""Monitor de tráfego para PyPanel Flask usando MySQL.

Dependências: pip install Flask mysql-connector-python
Configure MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
como variáveis de ambiente. Veja o README de integração no final do arquivo.
"""
import os, hashlib, secrets
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, current_app
import mysql.connector
from mysql.connector import Error

traffic_bp = Blueprint("traffic_monitor", __name__)
_SALT = os.environ.get("TRAFFIC_HASH_SALT") or secrets.token_hex(16)

def _connect():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "pypanel"),
        connection_timeout=5,
    )

def init_traffic_monitor(app):
    """Cria a tabela e registra coleta; chame uma vez após criar o app Flask."""
    with app.app_context():
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS site_traffic (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                visitor_hash CHAR(64) NOT NULL,
                path VARCHAR(512) NOT NULL,
                referrer VARCHAR(512) NULL,
                user_agent VARCHAR(255) NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_traffic_created (created_at),
                INDEX idx_traffic_visitor_created (visitor_hash, created_at),
                INDEX idx_traffic_path_created (path(191), created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            conn.commit()
            cur.close()
        finally:
            conn.close()
    app.register_blueprint(traffic_bp)

    @app.before_request
    def _capture_page_view():
        if request.method != "GET" or request.endpoint is None:
            return
        if request.endpoint.startswith("static") or request.path.startswith(("/traffic/api/", "/static/")):
            return
        if request.path in ("/favicon.ico", "/robots.txt"):
            return
        accept = request.headers.get("Accept", "")
        if "text/html" not in accept and request.path != "/":
            return
        # Não persiste o IP original; usa hash com segredo configurável.
        ip = request.remote_addr or "unknown"
        visitor_hash = hashlib.sha256((_SALT + ip).encode("utf-8")).hexdigest()
        path = request.path[:512]
        referrer = (request.referrer or "")[:512] or None
        agent = (request.user_agent.string or "")[:255] or None
        conn = None
        try:
            conn = _connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO site_traffic (visitor_hash,path,referrer,user_agent) VALUES (%s,%s,%s,%s)",
                        (visitor_hash, path, referrer, agent))
            conn.commit()
            cur.close()
        except Exception:
            current_app.logger.exception("Não foi possível registrar a visita")
        finally:
            if conn is not None:
                conn.close()

@traffic_bp.get("/traffic-monitor")
def traffic_monitor_page():
    return render_template("monitor.html")

@traffic_bp.get("/traffic/api/summary")
def traffic_summary():
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT
            (SELECT COUNT(DISTINCT visitor_hash) FROM site_traffic WHERE created_at >= NOW() - INTERVAL 5 MINUTE) AS active_visitors,
            (SELECT COUNT(*) FROM site_traffic WHERE DATE(created_at)=CURDATE()) AS page_views_today,
            (SELECT COUNT(DISTINCT visitor_hash) FROM site_traffic WHERE DATE(created_at)=CURDATE()) AS unique_visitors_today,
            (SELECT COUNT(*) / 60.0 FROM site_traffic WHERE created_at >= NOW() - INTERVAL 60 MINUTE) AS views_per_minute""")
        data = cur.fetchone() or {}
        cur.execute("SELECT path, COUNT(*) AS count FROM site_traffic WHERE DATE(created_at)=CURDATE() GROUP BY path ORDER BY count DESC LIMIT 8")
        data["top_pages"] = cur.fetchall()
        cur.close()
        return jsonify(data)
    except Error as e:
        current_app.logger.exception("Falha ao consultar resumo de tráfego")
        return jsonify(error="Não foi possível consultar o banco de dados."), 503
    finally:
        conn.close()

@traffic_bp.get("/traffic/api/series")
def traffic_series():
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT DATE_FORMAT(created_at, '%H:%i') AS label, COUNT(*) AS count
            FROM site_traffic WHERE created_at >= NOW() - INTERVAL 60 MINUTE
            GROUP BY YEAR(created_at), MONTH(created_at), DAY(created_at), HOUR(created_at), MINUTE(created_at)
            ORDER BY MINUTE(created_at)""")
        rows = cur.fetchall()
        # Completa os 60 minutos com zero para manter o gráfico temporal regular.
        buckets = {r["label"]: int(r["count"]) for r in rows}
        now = datetime.now().replace(second=0, microsecond=0)
        points = []
        for i in range(59, -1, -1):
            t = now - timedelta(minutes=i)
            label = t.strftime("%H:%M")
            points.append({"label": label, "count": buckets.get(label, 0)})
        cur.close()
        return jsonify(points=points)
    except Error:
        current_app.logger.exception("Falha ao consultar série de tráfego")
        return jsonify(error="Não foi possível consultar o banco de dados."), 503
    finally:
        conn.close()

@traffic_bp.get("/traffic/api/recent")
def traffic_recent():
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT DATE_FORMAT(created_at, '%d/%m/%Y %H:%i:%s') AS time,
            path, COALESCE(NULLIF(referrer,''),'Direto') AS referrer,
            COALESCE(NULLIF(user_agent,''),'Desconhecido') AS agent
            FROM site_traffic ORDER BY created_at DESC LIMIT 100""")
        visits = cur.fetchall()
        cur.close()
        return jsonify(visits=visits)
    except Error:
        current_app.logger.exception("Falha ao consultar visitas recentes")
        return jsonify(error="Não foi possível consultar o banco de dados."), 503
    finally:
        conn.close()