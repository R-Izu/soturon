$(function () {
    let localStream = null;
    let peer = null;
    let existingCall = null;

    // カメラ映像を取得
    navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: { exact: "environment" },
            width: { ideal: 640 },
            height: { ideal: 480 }
        },
        audio: false
    })
    .then((stream) => {
        localStream = stream;
        $('#myStream').get(0).srcObject = stream;
    })
    .catch((error) => {
        console.error('mediaDevice.getUserMedia() error:', error);
    });

    // SkyWayの初期化
    peer = new Peer({
        key: '3d69d042-3fa9-4f57-beb2-55e70d8c005a',
        debug: 3,
    });

    peer.on('open', () => {
        $('#my-id').text(peer.id);
    });

    $('#make-call').submit((e) => {
        e.preventDefault();
        const roomName = $('#join-room').val();
        if (!roomName) return;

        const call = peer.joinRoom(roomName, { mode: 'sfu', stream: localStream });
        setupCallEventHandlers(call);
    });

    function setupCallEventHandlers(call) {
        if (existingCall) existingCall.close();
        existingCall = call;
        $('#room-id').text(call.name);

        call.on('stream', (stream) => {
            const videoElement = document.getElementById('myStream');
            videoElement.srcObject = stream;
            videoElement.play();
        });

        call.on('close', () => {
            existingCall = null;
        });
    }

    // フルスクリーンボタンの動作
    $('#button1').on('click', function () {
        const videoElement = document.getElementById('myStream');
        if (videoElement.requestFullscreen) {
            videoElement.requestFullscreen();
        } else if (videoElement.webkitRequestFullscreen) {
            videoElement.webkitRequestFullscreen();
        } else if (videoElement.msRequestFullscreen) {
            videoElement.msRequestFullscreen();
        }
    });

    // 定期的に位置情報を送信する (1秒ごと)
    setInterval(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                // === スマホの現在時刻をミリ秒で取得 ===
                const nowMs = Date.now();  // or performance.now()

                const nowDate = new Date();
                const data = {
                    timestamp: nowMs,
                    year: nowDate.getFullYear(),
                    month: nowDate.getMonth() + 1,
                    day: nowDate.getDate(),
                    hour: nowDate.getHours(),
                    minute: nowDate.getMinutes(),
                    second: nowDate.getSeconds(),
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                };

                // POSTで送信 (fetchでサーバの /updateData に送る)
                fetch('/updateData', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                }).then(res => {
                    // console.log("位置情報送信完了");
                }).catch(err => {
                    console.error(err);
                });
            });
        }
    }, 1000);
});
