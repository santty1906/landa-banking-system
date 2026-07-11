(function () {
    "use strict";

    var stream = null;
    var capturedImages = {};
    var captureStep = "frontal";
    var mode = null;
    var animFrameId = null;
    var analysisTimer = null;
    var validFrameCount = 0;
    var countdownValue = 0;
    var countdownTimer = null;
    var isCapturing = false;
    var lastCaptureTime = 0;
    var loginUsername = "";
    var enrolling = false;
    var enrollmentComplete = false;
    var cameraLoading = false;

    var STEPS = ["frontal", "left", "right"];
    var REQUIRED_FRAMES = 10;
    var ANALYSIS_INTERVAL = 200;
    var MIN_BRIGHTNESS = 50;
    var MAX_BRIGHTNESS = 230;
    var MIN_SHARPNESS = 50;

    var supportsFaceDetector = "FaceDetector" in window;
    var faceDetector = null;
    if (supportsFaceDetector) {
        try {
            faceDetector = new FaceDetector({ fastMode: true });
        } catch (e) {
            supportsFaceDetector = false;
        }
    }

    var faceModal = document.getElementById("faceModal");
    var video = document.getElementById("faceVideo");
    var canvas = document.getElementById("faceCanvas");
    var instruction = document.getElementById("faceInstruction");
    var saveBtn = document.getElementById("saveFaceBtn");
    var status = document.getElementById("faceStatus");
    var guideRing = document.getElementById("faceGuideRing");
    var countdownEl = document.getElementById("faceCountdown");
    var statusBadge = document.getElementById("faceStatusBadge");
    var angleDots = document.querySelectorAll(".angle-dot");
    var preview = document.getElementById("facePreview");

    var enrollBtn = document.getElementById("enrollFaceBtn");
    var reEnrollBtn = document.getElementById("reEnrollFaceBtn");

    if (enrollBtn)
        enrollBtn.addEventListener("click", function () {
            startEnrollment();
        });
    if (reEnrollBtn)
        reEnrollBtn.addEventListener("click", function () {
            startEnrollment();
        });

    var retryBtn = document.getElementById("faceRetryBtn");
    if (retryBtn) {
        retryBtn.addEventListener("click", function () {
            console.log("[Face] Retry button clicked, re-attempting camera");
            hideRetryButton();
            hidePermissionWarning();
            hideHttpsWarning();
            setStatus("Requesting camera...", "info");
            startCamera();
        });
    }

    if (faceModal) {
        var bsModal = new bootstrap.Modal(faceModal);
        faceModal.addEventListener("hidden.bs.modal", function () {
            console.log("[Face] Modal hidden");
            stopCamera();
        });
        faceModal.addEventListener("shown.bs.modal", function () {
            console.log("[Face] Modal shown, mode:", mode, "enrollmentComplete:", enrollmentComplete);
            if ((mode === "enroll" || mode === "verify") && !enrollmentComplete) {
                startAnalysis();
            }
        });
    }

    function startEnrollment() {
        if (enrolling) {
            console.log("[Face] Enrollment already in progress, ignoring duplicate call");
            return;
        }
        if (enrollmentComplete) {
            console.log("[Face] Enrollment already completed, resetting state");
            enrollmentComplete = false;
        }
        console.log("[Face] Starting enrollment");
        mode = "enroll";
        capturedImages = {};
        captureStep = "frontal";
        validFrameCount = 0;
        isCapturing = false;
        enrolling = false;
        if (preview) preview.innerHTML = "";
        if (saveBtn) {
            saveBtn.classList.add("d-none");
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check2 me-1"></i>Save';
        }
        setInstruction("Look straight ahead");
        setStatus("Position your face in the circle", "info");
        updateAngleDots();
        startCamera();
        if (bsModal) bsModal.show();
    }

    function startVerification(username) {
        mode = "verify";
        loginUsername = username || "";
        capturedImages = {};
        validFrameCount = 0;
        isCapturing = false;
        setInstruction("Look at the camera");
        setStatus("Position your face in the circle", "info");
        startCamera();
        if (bsModal) bsModal.show();
    }

    async function startCamera() {
        if (cameraLoading) return;
        if (!window.isSecureContext && location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
            console.warn("[Face] Insecure context - camera requires HTTPS");
            setStatus("Camera requires HTTPS. Please use https:// or localhost.", "error");
            setInstruction("Secure connection needed");
            showHttpsWarning();
            return;
        }
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn("[Face] getUserMedia not supported");
            setStatus("Camera not supported on this browser.", "error");
            setInstruction("Unsupported browser");
            return;
        }
        cameraLoading = true;
        showCameraLoading();
        console.log("[Face] Requesting camera access");
        try {
            var constraints = {
                video: {
                    facingMode: "user",
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                },
                audio: false,
            };
            if (navigator.permissions && navigator.permissions.query) {
                try {
                    var permStatus = await navigator.permissions.query({ name: "camera" });
                    if (permStatus.state === "denied") {
                        console.warn("[Face] Camera permission permanently denied");
                        setStatus("Camera permission denied. Please enable it in browser settings.", "error");
                        setInstruction("Permission blocked");
                        cameraLoading = false;
                        hideCameraLoading();
                        showPermissionWarning();
                        return;
                    }
                    if (permStatus.state === "prompt") {
                        console.log("[Face] Camera permission state: prompt (will request)");
                    }
                    if (permStatus.state === "granted") {
                        console.log("[Face] Camera permission already granted");
                    }
                } catch (permErr) {
                    console.log("[Face] Permissions API not supported for camera");
                }
            }
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log("[Face] Camera stream obtained");
            video.srcObject = stream;
            video.setAttribute("playsinline", "true");
            video.setAttribute("webkit-playsinline", "true");
            video.setAttribute("autoplay", "true");
            video.setAttribute("muted", "true");
            await video.play();
            console.log("[Face] Video playback started");
            cameraLoading = false;
            hideCameraLoading();
            if (mode === "enroll" || mode === "verify") {
                startAnalysis();
            }
        } catch (err) {
            cameraLoading = false;
            hideCameraLoading();
            console.error("[Face] Camera error:", err.name, err.message);
            if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                setStatus("Camera permission denied. Tap allow when prompted, then retry.", "error");
                setInstruction("Permission required");
                showPermissionWarning();
            } else if (err.name === "NotFoundError") {
                setStatus("No camera found on this device.", "error");
                setInstruction("Camera unavailable");
            } else if (err.name === "NotReadableError") {
                setStatus("Camera is busy. Close other apps using the camera.", "error");
                setInstruction("Camera busy");
            } else if (err.name === "OverconstrainedError") {
                setStatus("Camera does not meet requirements. Try a different device.", "error");
                setInstruction("Camera incompatible");
            } else {
                setStatus("Camera access failed: " + (err.message || "unknown error"), "error");
                setInstruction("Camera unavailable");
            }
            showRetryButton();
        }
    }

    function stopCamera() {
        console.log("[Face] Stopping camera");
        isCapturing = false;
        enrolling = false;
        cameraLoading = false;
        if (analysisTimer) {
            clearInterval(analysisTimer);
            analysisTimer = null;
        }
        if (countdownTimer) {
            clearInterval(countdownTimer);
            countdownTimer = null;
        }
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
        }
        if (stream) {
            stream.getTracks().forEach(function (t) {
                t.stop();
            });
            stream = null;
        }
        video.srcObject = null;
        validFrameCount = 0;
        mode = null;
        if (guideRing) {
            guideRing.className = "face-guide-ring";
        }
        if (countdownEl) countdownEl.style.display = "none";
        hideCameraLoading();
        hideRetryButton();
        hidePermissionWarning();
        hideHttpsWarning();
    }

    function startAnalysis() {
        if (analysisTimer) clearInterval(analysisTimer);
        analysisTimer = setInterval(analyzeFrame, ANALYSIS_INTERVAL);
    }

    async function analyzeFrame() {
        if (
            isCapturing ||
            enrolling ||
            enrollmentComplete ||
            !video ||
            !video.videoWidth ||
            !video.videoHeight
        )
            return;

        var ctx = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        var brightness = getBrightness(canvas, ctx);
        var sharpness = getSharpness(canvas, ctx);

        if (brightness < MIN_BRIGHTNESS) {
            setGuideState("invalid");
            setStatus("Need more light", "warning");
            validFrameCount = 0;
            return;
        }

        if (brightness > MAX_BRIGHTNESS) {
            setGuideState("invalid");
            setStatus("Too bright", "warning");
            validFrameCount = 0;
            return;
        }

        if (sharpness < MIN_SHARPNESS) {
            setGuideState("invalid");
            setStatus("Hold steady", "warning");
            validFrameCount = 0;
            return;
        }

        var faceOk = false;
        if (supportsFaceDetector) {
            try {
                var faces = await faceDetector.detect(canvas);
                if (faces.length === 1) {
                    var f = faces[0];
                    faceOk = isFaceCentered(f, canvas.width, canvas.height);
                } else if (faces.length > 1) {
                    setGuideState("invalid");
                    setStatus("Only one face please", "warning");
                    validFrameCount = 0;
                    return;
                } else {
                    setGuideState("invalid");
                    setStatus("Face not detected", "warning");
                    validFrameCount = 0;
                    return;
                }
            } catch (e) {
                faceOk = checkCenterVariance(canvas, ctx);
            }
        } else {
            faceOk = checkCenterVariance(canvas, ctx);
        }

        if (!faceOk) {
            setGuideState("invalid");
            setStatus("Center your face", "warning");
            validFrameCount = 0;
            return;
        }

        setGuideState("valid");
        setStatus("Face detected", "success");
        validFrameCount++;

        if (
            validFrameCount >= REQUIRED_FRAMES &&
            !isCapturing
        ) {
            startCountdown();
        }
    }

    function isFaceCentered(face, vw, vh) {
        var cx = face.boundingBox.x + face.boundingBox.width / 2;
        var cy = face.boundingBox.y + face.boundingBox.height / 2;
        var centerX = vw / 2;
        var centerY = vh / 2;
        var maxDist = Math.min(vw, vh) * 0.25;
        var dist = Math.sqrt(
            (cx - centerX) * (cx - centerX) +
                (cy - centerY) * (cy - centerY)
        );
        if (dist > maxDist) return false;
        var faceW = face.boundingBox.width;
        var faceH = face.boundingBox.height;
        var minSize = Math.min(vw, vh) * 0.15;
        var maxSize = Math.min(vw, vh) * 0.6;
        if (faceW < minSize || faceH < minSize) return false;
        if (faceW > maxSize || faceH > maxSize) return false;
        return true;
    }

    function checkCenterVariance(canvas, ctx) {
        var cx = Math.floor(canvas.width / 2);
        var cy = Math.floor(canvas.height / 2);
        var r = Math.floor(Math.min(canvas.width, canvas.height) * 0.15);
        var imageData = ctx.getImageData(
            Math.max(0, cx - r),
            Math.max(0, cy - r),
            Math.min(r * 2, canvas.width),
            Math.min(r * 2, canvas.height)
        );
        var data = imageData.data;
        var sum = 0,
            sumSq = 0,
            count = 0;
        for (var i = 0; i < data.length; i += 4) {
            var gray =
                0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            sum += gray;
            sumSq += gray * gray;
            count++;
        }
        var mean = sum / count;
        var variance = sumSq / count - mean * mean;

        var edgeVariance = getEdgeVariance(canvas, ctx);
        if (variance < 200) return false;
        if (edgeVariance > 0 && variance / edgeVariance < 1.5) return false;
        return true;
    }

    function getEdgeVariance(canvas, ctx) {
        var w = canvas.width,
            h = canvas.height;
        var margin = Math.floor(Math.min(w, h) * 0.1);
        var regions = [
            { x: 0, y: 0, w: margin, h: h },
            { x: w - margin, y: 0, w: margin, h: h },
            { x: 0, y: 0, w: w, h: margin },
            { x: 0, y: h - margin, w: w, h: margin },
        ];
        var totalVar = 0,
            count = 0;
        for (var r = 0; r < regions.length; r++) {
            var reg = regions[r];
            var imageData = ctx.getImageData(reg.x, reg.y, reg.w, reg.h);
            var data = imageData.data;
            var s = 0,
                sq = 0,
                c = 0;
            for (var i = 0; i < data.length; i += 4) {
                var gray =
                    0.299 * data[i] +
                    0.587 * data[i + 1] +
                    0.114 * data[i + 2];
                s += gray;
                sq += gray * gray;
                c++;
            }
            if (c > 0) {
                var m = s / c;
                totalVar += sq / c - m * m;
                count++;
            }
        }
        return count > 0 ? totalVar / count : 0;
    }

    function getBrightness(canvas, ctx) {
        var w = Math.min(canvas.width, 80);
        var h = Math.min(canvas.height, 60);
        var imageData = ctx.getImageData(
            Math.floor((canvas.width - w) / 2),
            Math.floor((canvas.height - h) / 2),
            w,
            h
        );
        var data = imageData.data;
        var sum = 0,
            count = 0;
        for (var i = 0; i < data.length; i += 4) {
            sum +=
                0.299 * data[i] +
                0.587 * data[i + 1] +
                0.114 * data[i + 2];
            count++;
        }
        return sum / count;
    }

    function getSharpness(canvas, ctx) {
        var w = Math.min(canvas.width, 160);
        var h = Math.min(canvas.height, 120);
        var imageData = ctx.getImageData(
            Math.floor((canvas.width - w) / 2),
            Math.floor((canvas.height - h) / 2),
            w,
            h
        );
        var data = imageData.data;
        var sumSq = 0,
            count = 0;
        for (var y = 1; y < h - 1; y++) {
            for (var x = 1; x < w - 1; x++) {
                var idx = (y * w + x) * 4;
                var gray =
                    0.299 * data[idx] +
                    0.587 * data[idx + 1] +
                    0.114 * data[idx + 2];
                var topIdx = ((y - 1) * w + x) * 4;
                var bottomIdx = ((y + 1) * w + x) * 4;
                var leftIdx = (y * w + (x - 1)) * 4;
                var rightIdx = (y * w + (x + 1)) * 4;
                var lap =
                    4 * gray -
                    (0.299 * data[topIdx] +
                        0.587 * data[topIdx + 1] +
                        0.114 * data[topIdx + 2]) -
                    (0.299 * data[bottomIdx] +
                        0.587 * data[bottomIdx + 1] +
                        0.114 * data[bottomIdx + 2]) -
                    (0.299 * data[leftIdx] +
                        0.587 * data[leftIdx + 1] +
                        0.114 * data[leftIdx + 2]) -
                    (0.299 * data[rightIdx] +
                        0.587 * data[rightIdx + 1] +
                        0.114 * data[rightIdx + 2]);
                sumSq += lap * lap;
                count++;
            }
        }
        return count > 0 ? sumSq / count : 0;
    }

    function startCountdown() {
        if (enrolling || enrollmentComplete) {
            console.log("[Face] Countdown blocked - enrollment already complete or in progress");
            return;
        }
        isCapturing = true;
        countdownValue = 3;
        if (countdownEl) {
            countdownEl.style.display = "block";
            countdownEl.textContent = countdownValue;
        }
        setGuideState("countdown");
        setStatus("Capturing in " + countdownValue + "...", "info");
        console.log("[Face] Starting countdown, step:", captureStep);

        countdownTimer = setInterval(function () {
            countdownValue--;
            if (countdownEl) countdownEl.textContent = countdownValue;
            if (countdownValue <= 0) {
                clearInterval(countdownTimer);
                countdownTimer = null;
                doCapture();
            }
        }, 800);
    }

    function doCapture() {
        if (enrolling || enrollmentComplete) {
            console.log("[Face] Capture blocked - enrollment already done");
            return;
        }
        if (countdownEl) countdownEl.style.display = "none";
        setGuideState("capturing");
        setStatus("Captured!", "success");
        var ctx = canvas.getContext("2d");

        // Redimensionar a un máximo de 640px en el lado más largo: el
        // reconocimiento facial no necesita más resolución que esa, y
        // enviar la foto completa de la cámara de un celular (a veces
        // 3000px+ de ancho) ralentiza tanto la subida como el análisis
        // en el servidor (RetinaFace + Facenet512 + anti-spoofing).
        var MAX_DIM = 640;
        var scale = Math.min(1, MAX_DIM / Math.max(video.videoWidth, video.videoHeight));
        var outW = Math.round(video.videoWidth * scale);
        var outH = Math.round(video.videoHeight * scale);

        canvas.width = outW;
        canvas.height = outH;
        ctx.drawImage(video, 0, 0, outW, outH);
        var dataUrl = canvas.toDataURL("image/jpeg", 0.85);

        if (mode === "enroll") {
            capturedImages[captureStep] = dataUrl;
            addPreviewThumb(dataUrl);

            var currentIdx = STEPS.indexOf(captureStep);
            if (currentIdx < STEPS.length - 1) {
                captureStep = STEPS[currentIdx + 1];
                console.log("[Face] Captured", captureStep, "- advancing to", STEPS[currentIdx + 1]);
                var labels = {
                    frontal: "Look straight ahead",
                    left: "Turn slightly left",
                    right: "Turn slightly right",
                };
                setInstruction(labels[captureStep]);
                setStatus(
                    "Angle " +
                        (currentIdx + 2) +
                        " of " +
                        STEPS.length,
                    "info"
                );
                updateAngleDots();
                setTimeout(function () {
                    validFrameCount = 0;
                    isCapturing = false;
                }, 500);
            } else {
                enrolling = true;
                console.log("[Face] All 3 angles captured, enrolling...");
                setInstruction("All angles captured!");
                setStatus("3/3 captured. Saving...", "success");
                updateAngleDots();
                setTimeout(function () {
                    saveEnrollment();
                }, 600);
            }
        } else if (mode === "verify") {
            setStatus("Verifying...", "info");
            sendVerification(dataUrl);
        }
    }

    function addPreviewThumb(dataUrl) {
        if (!preview) return;
        var img = document.createElement("img");
        img.src = dataUrl;
        img.className = "rounded-2 border";
        img.style.width = "70px";
        img.style.height = "70px";
        img.style.objectFit = "cover";
        preview.appendChild(img);
    }

    function updateAngleDots() {
        angleDots.forEach(function (dot, i) {
            dot.className = "angle-dot";
            var stepName = STEPS[i];
            if (stepName === captureStep) {
                dot.classList.add("active");
            }
            if (capturedImages[stepName]) {
                dot.classList.add("done");
            }
        });
    }

    function saveEnrollment() {
        if (enrollmentComplete) {
            console.log("[Face] Enrollment already completed, skipping save");
            return;
        }
        console.log("[Face] Sending enrollment to server");
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML =
                '<span class="spinner-border spinner-border-sm"></span> Saving...';
        }
        fetch("/auth/../api/face/enroll", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ images: capturedImages }),
        })
            .then(function (resp) {
                if (resp.ok) {
                    console.log("[Face] Enrollment API success, response OK");
                    enrollmentComplete = true;
                    enrolling = false;
                    setStatus("Face enrolled successfully!", "success");
                    setInstruction("Enrollment complete");
                    stopCamera();
                    if (saveBtn) {
                        saveBtn.disabled = true;
                        saveBtn.innerHTML =
                            '<i class="bi bi-check2 me-1"></i>Enrolled';
                    }
                    setTimeout(function () {
                        if (bsModal) bsModal.hide();
                        location.reload();
                    }, 1200);
                } else {
                    return resp.json().then(function (data) {
                        throw new Error(
                            data.error || "Enrollment failed"
                        );
                    });
                }
            })
            .catch(function (err) {
                console.error("[Face] Enrollment error:", err.message);
                setStatus(err.message || "Enrollment failed", "error");
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML =
                        '<i class="bi bi-arrow-clockwise me-1"></i>Retry';
                }
                enrolling = false;
                isCapturing = false;
                validFrameCount = 0;
                if (analysisTimer) {
                    clearInterval(analysisTimer);
                    analysisTimer = null;
                }
                if (countdownTimer) {
                    clearInterval(countdownTimer);
                    countdownTimer = null;
                }
            });
    }

    function sendVerification(dataUrl) {
        var endpoint = loginUsername
            ? "/auth/../api/face/login-verify"
            : "/auth/../api/face/verify";
        var body = loginUsername
            ? { image: dataUrl, username: loginUsername }
            : { image: dataUrl };

        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        })
            .then(function (resp) {
                if (resp.ok) {
                    setStatus("Face verified! Redirecting...", "success");
                    setInstruction("Access granted");
                    setTimeout(function () {
                        if (bsModal) bsModal.hide();
                        window.location.href = "/dashboard";
                    }, 1000);
                } else {
                    return resp.json().then(function (data) {
                        var msg =
                            data.error || "Face does not match. Try again.";
                        setStatus(msg, "error");
                        setInstruction("Try again");
                        setTimeout(function () {
                            isCapturing = false;
                            validFrameCount = 0;
                        }, 5000);
                    });
                }
            })
            .catch(function () {
                setStatus("Network error. Try again.", "error");
                setTimeout(function () {
                    isCapturing = false;
                    validFrameCount = 0;
                }, 5000);
            });
    }

    function setInstruction(text) {
        if (instruction) instruction.textContent = text;
    }

    function setStatus(text, type) {
        if (status) {
            status.textContent = text;
            status.className = "mt-2 small";
        }
        if (statusBadge) {
            statusBadge.textContent = text;
            statusBadge.className = "face-status-badge";
            if (type) statusBadge.classList.add(type);
            statusBadge.style.display = "block";
        }
    }

    function setGuideState(state) {
        if (!guideRing) return;
        guideRing.className = "face-guide-ring";
        if (state) guideRing.classList.add(state);
    }

    function showCameraLoading() {
        if (!guideRing) return;
        var existing = document.getElementById("faceLoadingSpinner");
        if (existing) return;
        var el = document.createElement("div");
        el.id = "faceLoadingSpinner";
        el.className = "face-loading-spinner";
        el.innerHTML =
            '<div class="spinner"></div><small>Starting camera...</small>';
        guideRing.parentElement.appendChild(el);
    }

    function hideCameraLoading() {
        var el = document.getElementById("faceLoadingSpinner");
        if (el) el.remove();
    }

    function showPermissionWarning() {
        hideCameraLoading();
        var existing = document.getElementById("facePermissionWarning");
        if (existing) return;
        if (!status) return;
        var el = document.createElement("div");
        el.id = "facePermissionWarning";
        el.className = "face-permission-warning";
        el.innerHTML =
            '<strong><i class="bi bi-camera-video-off me-1"></i>Camera permission needed</strong>' +
            "<small>Please allow camera access in your browser settings, then tap Retry below.</small>";
        if (status.parentElement) status.parentElement.insertBefore(el, status);
    }

    function hidePermissionWarning() {
        var el = document.getElementById("facePermissionWarning");
        if (el) el.remove();
    }

    function showHttpsWarning() {
        hideCameraLoading();
        var existing = document.getElementById("faceHttpsWarning");
        if (existing) return;
        if (!guideRing) return;
        var el = document.createElement("div");
        el.id = "faceHttpsWarning";
        el.className = "face-https-warning";
        el.innerHTML =
            '<i class="bi bi-shield-exclamation"></i>' +
            "<strong>HTTPS Required</strong>" +
            "<small>Camera access requires a secure connection (HTTPS) or localhost. " +
            "Please access this site via https:// or use localhost during development.</small>";
        guideRing.parentElement.appendChild(el);
    }

    function hideHttpsWarning() {
        var el = document.getElementById("faceHttpsWarning");
        if (el) el.remove();
    }

    function showRetryButton() {
        if (retryBtn) {
            retryBtn.classList.remove("d-none");
        }
    }

    function hideRetryButton() {
        if (retryBtn) {
            retryBtn.classList.add("d-none");
        }
    }

    window.LandaFace = {
        verify: async function (imageDataUrl) {
            try {
                var resp = await fetch("/auth/../api/face/verify", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ image: imageDataUrl }),
                });
                return resp.ok;
            } catch (e) {
                return false;
            }
        },
        startVerification: startVerification,
        startEnrollment: startEnrollment,
        checkUserFace: function (username) {
            return fetch(
                "/auth/../api/face/check-user?username=" +
                    encodeURIComponent(username)
            ).then(function (r) {
                return r.json();
            });
        },
    };

    var loginFaceBtn = document.getElementById("loginFaceBtn");
    if (loginFaceBtn) {
        loginFaceBtn.addEventListener("click", function () {
            var userInput = document.getElementById("loginUsername");
            var username = userInput
                ? userInput.value.trim()
                : "";
            if (!username) {
                userInput.focus();
                userInput.classList.add("is-invalid");
                return;
            }
            startVerification(username);
        });
    }

    var loginUsernameInput = document.getElementById("loginUsername");
    if (loginUsernameInput) {
        loginUsernameInput.addEventListener("blur", function () {
            var val = this.value.trim();
            if (val.length < 2) return;
            fetch(
                "/auth/../api/face/check-user?username=" +
                    encodeURIComponent(val)
            )
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    var faceSection = document.getElementById(
                        "faceLoginSection"
                    );
                    if (faceSection) {
                        faceSection.style.display = data.enrolled
                            ? "block"
                            : "none";
                    }
                })
                .catch(function () {});
        });
    }
})();
