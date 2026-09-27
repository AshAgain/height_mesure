import cv2
import numpy as np

img = cv2.imread("image3.jpg")

if img is None:
    print("Ошибка: не найдено изображение")
    exit()

scale_display = 0.6
img_display = cv2.resize(img, None, fx=scale_display, fy=scale_display)

points = []

# =========================
# ЛУПА
# =========================
def draw_zoom(x, y):
    zoom_size = 30
    zoom_scale = 6

    x_real = int(x / scale_display)
    y_real = int(y / scale_display)

    x1 = max(0, x_real - zoom_size)
    y1 = max(0, y_real - zoom_size)
    x2 = min(img.shape[1], x_real + zoom_size)
    y2 = min(img.shape[0], y_real + zoom_size)

    zoom = img[y1:y2, x1:x2].copy()

    if zoom.size == 0:
        return

    zoom = cv2.resize(zoom, None, fx=zoom_scale, fy=zoom_scale)

    # точки только в зуме
    for px, py in points:
        if x1 <= px <= x2 and y1 <= py <= y2:
            zx = int((px - x1) * zoom_scale)
            zy = int((py - y1) * zoom_scale)
            cv2.circle(zoom, (zx, zy), 4, (0, 0, 255), -1)

    # курсор
    h, w = zoom.shape[:2]
    cx, cy = w // 2, h // 2

    cv2.line(zoom, (cx - 10, cy), (cx + 10, cy), (0, 255, 0), 1)
    cv2.line(zoom, (cx, cy - 10), (cx, cy + 10), (0, 255, 0), 1)

    cv2.imshow("zoom", zoom)


# =========================
# РИСОВАНИЕ ЧЕРТЕЖА
# =========================
def draw_measurements():
    canvas = img_display.copy()

    def draw_pair(pA, pB, text):
            x1 = int(pA[0] * scale_display)
            y1 = int(pA[1] * scale_display)
            x2 = int(pB[0] * scale_display)
            y2 = int(pB[1] * scale_display)

            color_line = (0, 0, 255)        # тёмные линии
            color_text = (0, 220, 255)       # голубой текст

            # линия
            cv2.line(canvas, (x1, y1), (x2, y2), color_line, 1)

            # усики
            size = 8
            cv2.line(canvas, (x1 - size, y1), (x1 + size, y1), color_line, 1)
            cv2.line(canvas, (x2 - size, y2), (x2 + size, y2), color_line, 1)

            # позиция текста
            mx = (x1 + x2) // 2
            my = (y1 + y2) // 2

            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.5
            thickness = 1

            # размер текста
            (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)

            # --- подложка (полупрозрачная) ---
            overlay = canvas.copy()
            cv2.rectangle(overlay,
                        (mx + 5, my - th - 8),
                        (mx + tw + 12, my + 4),
                        (255, 255, 255),
                        -1)

            # прозрачность
            alpha = 0.7
            cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)

            # --- контур текста (чёрный) ---
            cv2.putText(canvas, text,
                        (mx + 8, my - 2),
                        font,
                        scale,
                        (0, 0, 0),
                        3,
                        cv2.LINE_AA)

            # --- основной текст ---
            cv2.putText(canvas, text,
                        (mx + 8, my - 2),
                        font,
                        scale,
                        color_text,
                        1,
                        cv2.LINE_AA)
    # рисуем только если есть масштаб
    if len(points) >= 2:
        p1, p2 = points[0], points[1]
        pixel_dist = np.linalg.norm(np.array(p1) - np.array(p2))
        scale = 1.0 / pixel_dist

        def measure(a, b):
            return np.linalg.norm(np.array(a) - np.array(b)) * scale

        # пары измерений
        pairs = [
            (2, 3, "H1"),
            (4, 5, "H2"),
            (6, 7, "H3"),
        ]

        for i, j, label in pairs:
            if len(points) > j:
                value = measure(points[i], points[j])
                draw_pair(points[i], points[j], f"{label}: {value:.2f} mm")

    cv2.imshow("img", canvas)


# =========================
# КЛИК
# =========================
def click(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        draw_zoom(x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        real_x = int(x / scale_display)
        real_y = int(y / scale_display)

        points.append((real_x, real_y))
        print(f"Точка {len(points)} добавлена")

        draw_measurements()


# =========================
# ИНТЕРФЕЙС
# =========================
cv2.imshow("img", img_display)
cv2.setMouseCallback("img", click)

print("Сделай 8 кликов:")
print("1-2: масштаб (1 мм)")
print("3-4: высота 1")
print("5-6: высота 2")
print("7-8: высота 3")

cv2.waitKey(0)
cv2.destroyAllWindows()

# =========================
# РАСЧЁТ
# =========================
if len(points) < 8:
    print("Ошибка: нужно 8 точек")
    exit()

p1, p2 = points[0], points[1]

pixel_dist_ref = np.linalg.norm(np.array(p1) - np.array(p2))
scale = 1.0 / pixel_dist_ref

def measure(pA, pB):
    px = np.linalg.norm(np.array(pA) - np.array(pB))
    return px * scale

h1 = measure(points[2], points[3])
h2 = measure(points[4], points[5])
h3 = measure(points[6], points[7])

print(f"\nМасштаб: {scale:.5f} мм/пиксель")
print(f"Высота 1: {h1:.2f} мм")
print(f"Высота 2: {h2:.2f} мм")
print(f"Высота 3: {h3:.2f} мм")