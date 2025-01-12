const express = require('express');
const bodyParser = require('body-parser');
const WebSocket = require('ws');
const path = require('path');

//---------------------------
//  オブジェクト指向の構造
//---------------------------
class MobileVideoServer {
    constructor(httpPort, wsPort) {
        this.httpPort = httpPort;
        this.wsPort = wsPort;

        this.app = express();
        this.server = null;
        this.wss = null;

        this.latestData = {
            timestamp: null,   // スマホが取得した時刻
            year: null,
            month: null,
            day: null,
            hour: null,
            minute: null,
            second: null,
            latitude: null,
            longitude: null
        };
    }

    init() {
        // 静的ファイル (public フォルダ) の提供
        this.app.use(express.static(path.join(__dirname, 'public')));
        this.app.use(bodyParser.json());

        // HTTPサーバ
        this.server = this.app.listen(this.httpPort, () => {
            console.log(`HTTPサーバが http://localhost:${this.httpPort} で起動しました`);
        });

        // WebSocketサーバ
        this.wss = new WebSocket.Server({ port: this.wsPort }, () => {
            console.log(`WebSocketサーバが ws://localhost:${this.wsPort} で起動しました`);
        });

        // WebSocketクライアント接続時の処理
        this.wss.on('connection', (ws) => this.onClientConnected(ws));

        // 位置情報更新API
        this.app.post('/updateData', (req, res) => this.onUpdateData(req, res));
    }

    onClientConnected(ws) {
        console.log('Unity クライアントが接続しました。');

        // 定期送信（ここでは 1秒ごと）
        const interval = setInterval(() => {
            if (this.latestData.year !== null && this.latestData.latitude !== null) {
                // カンマ区切りフォーマットに加えて、timestampも付与
                const formattedData = [
                    this.latestData.timestamp,  // 先頭にスマホのtimestamp (ミリ秒)
                    this.latestData.year,
                    this.latestData.month,
                    this.latestData.day,
                    this.latestData.hour,
                    this.latestData.minute,
                    this.latestData.second,
                    this.latestData.latitude,
                    this.latestData.longitude
                ].join(',');

                ws.send(formattedData);
                console.log(`送信データ: ${formattedData}`);
            }
        }, 1000);

        ws.on('close', () => {
            clearInterval(interval);
            console.log('Unity クライアントが切断されました。');
        });
    }

    onUpdateData(req, res) {
        const {
            timestamp, // ← スマホから送られるタイムスタンプ (Date.now()など)
            year, month, day, hour, minute, second, latitude, longitude
        } = req.body;

        // データを保存
        this.latestData.timestamp = timestamp;
        this.latestData.year = year;
        this.latestData.month = month;
        this.latestData.day = day;
        this.latestData.hour = hour;
        this.latestData.minute = minute;
        this.latestData.second = second;
        this.latestData.latitude = parseFloat(latitude).toFixed(6);
        this.latestData.longitude = parseFloat(longitude).toFixed(6);

        res.sendStatus(200);
    }
}

//---------------------------
// 実行部
//---------------------------
const HTTP_PORT = 8081;
const WS_PORT = 8082;

const server = new MobileVideoServer(HTTP_PORT, WS_PORT);
server.init();
