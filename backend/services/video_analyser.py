
import cv2
import numpy as np
import mediapipe as mp
from collections import Counter

# Lazy import DeepFace to avoid slow startup if not needed
_deepface_available = True
try:
    from deepface import DeepFace
except ImportError:
    _deepface_available = False
    print("[ORION] DeepFace not available — emotion analysis disabled")

mp_face_mesh = mp.solutions.face_mesh
mp_pose     = mp.solutions.pose


# MediaPipe landmark indices
# Left eye outer / inner corners
LEFT_EYE  = [33, 133]
RIGHT_EYE = [362, 263]
NOSE_TIP  = 1


def analyse_video(video_path: str, sample_every_n_frames: int = 15) -> dict:
    """
    Samples every N frames from the video and returns non-verbal metrics.
    sample_every_n_frames=15 at 30fps = analyse 2 frames/sec.
    """
    metrics = {}
    cap = cv2.VideoCapture(video_path)
    fps  = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    face_detected_frames  = 0
    on_camera_frames      = 0
    good_posture_frames   = 0
    total_sampled         = 0
    emotion_counts        = Counter()
    head_yaw_values       = []
    mouth_movement_values = []

    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    )
    pose_detector = mp_pose.Pose(
        static_image_mode=True,
        min_detection_confidence=0.5,
    )

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % sample_every_n_frames != 0:
            continue

        total_sampled += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ── Face Mesh ─────────────────────────────────────────────────────────
        face_result = face_mesh.process(rgb)
        if face_result.multi_face_landmarks:
            face_detected_frames += 1
            landmarks = face_result.multi_face_landmarks[0].landmark
            # Mouth movement (simple lip distance)
            upper_lip = landmarks[13]
            lower_lip = landmarks[14]
            lip_gap = abs(upper_lip.y - lower_lip.y)

            mouth_movement_values.append(lip_gap)
            h, w = frame.shape[:2]

            # Gaze proxy: compare horizontal nose position to eye averagepoint
            nose = landmarks[NOSE_TIP]
            left_eye_x  = np.mean([landmarks[i].x for i in LEFT_EYE])
            right_eye_x = np.mean([landmarks[i].x for i in RIGHT_EYE])
            eye_center_x = (left_eye_x + right_eye_x) / 2.0
            yaw_offset = abs(nose.x - eye_center_x)
            head_yaw_values.append(yaw_offset)

            # If yaw offset is small → facing camera
            if yaw_offset < 0.05:
                on_camera_frames += 1

            # ── Emotion (DeepFace, sample every 5th analysed frame) ───────────
            if _deepface_available and total_sampled % 5 == 0:
                try:
                    analysis = DeepFace.analyze(
                        rgb,
                        actions=["emotion"],
                        enforce_detection=False,
                        silent=True,
                    )
                    dominant = analysis[0]["dominant_emotion"]
                    emotion_counts[dominant] += 1
                except Exception:
                    pass

        # ── Posture (MediaPipe Pose) ───────────────────────────────────────────
        pose_result = pose_detector.process(rgb)
        if pose_result.pose_landmarks:
            lm = pose_result.pose_landmarks.landmark
            mp_pose_enum = mp.solutions.pose.PoseLandmark
            # Shoulders should be roughly level
            left_shoulder  = lm[mp_pose_enum.LEFT_SHOULDER]
            right_shoulder = lm[mp_pose_enum.RIGHT_SHOULDER]
            shoulder_tilt = abs(left_shoulder.y - right_shoulder.y)
            # Also check head is not too bowed (nose landmark)
            nose_y = lm[mp_pose_enum.NOSE].y
            average_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
            head_drop = average_shoulder_y - nose_y

            if shoulder_tilt < 0.05 and head_drop > 0.1:
                good_posture_frames += 1

    cap.release()
    face_mesh.close()
    pose_detector.close()
    # Detect if person is visually speaking
    if mouth_movement_values:
        avg_movement = np.mean(mouth_movement_values)
    else:
        avg_movement = 0.0

    movement_std = np.std(mouth_movement_values) if mouth_movement_values else 0.0

    is_visually_speaking = (avg_movement > 0.02) and (movement_std > 0.005)
    
    # ── Compute scores ────────────────────────────────────────────────────────
    presence_rate = face_detected_frames / max(total_sampled, 1)
    eye_contact_pct = (on_camera_frames / max(face_detected_frames, 1)) * 100
    posture_pct     = (good_posture_frames / max(total_sampled, 1)) * 100
    mean_yaw        = float(np.mean(head_yaw_values)) if head_yaw_values else 0.5

    # Distraction = frames where face was absent + off-camera frames
    distraction_events = (total_sampled - face_detected_frames) + (face_detected_frames - on_camera_frames)

    metrics["total_frames_sampled"]  = total_sampled
    metrics["face_detected_pct"]     = round(presence_rate * 100, 1)
    metrics["eye_contact_pct"]       = round(eye_contact_pct, 1)
    metrics["posture_score"]         = round(posture_pct, 1)
    metrics["distraction_events"]    = distraction_events
    metrics["mean_head_yaw"]         = round(mean_yaw, 4)

    # Dominant emotion
    if emotion_counts:
        dominant_emotion = emotion_counts.most_common(1)[0][0]
        metrics["dominant_emotion"] = dominant_emotion
        # Map emotions to confidence proxy
        positive = {"neutral", "happy", "surprise"}
        metrics["positive_emotion_pct"] = round(
            sum(emotion_counts[e] for e in positive) / sum(emotion_counts.values()) * 100, 1
        )
    else:
        metrics["dominant_emotion"]    = "unknown"
        metrics["positive_emotion_pct"] = 50.0

    # Nonverbal score formula
    nonverbal_score = round(
        0.40 * (eye_contact_pct) +
        0.30 * posture_pct       +
        0.20 * metrics["positive_emotion_pct"] +
        0.10 * (presence_rate * 100),
        1,
    )
    metrics["nonverbal_score"] = max(0.0, min(100.0, nonverbal_score))
    metrics["visual_speaking"] = is_visually_speaking
    return metrics
