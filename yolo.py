import cv2
from ultralytics import YOLO
import sys

def run_ppe_detection():
    # 1. 加载模型
    # 确保 'yolo9e.pt' 在当前目录下，或者是绝对路径
    print("正在加载模型，请稍候...")
    try:
        model = YOLO("yolo9e.pt")
    except Exception as e:
        print(f"错误：无法加载模型。请确认 'yolo9e.pt' 文件存在。\n详细错误: {e}")
        return

    # 2. 调用 MacBook 摄像头
    #通常 0 是默认摄像头。如果你的 Mac 连接了多个摄像头（如外接显示器），可能需要改为 1
    cap = cv2.VideoCapture(1)

    #Mac 这里的设置有时候有助于提高兼容性 (如果不工作可以尝试去掉这行)
    # cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        print("错误：无法打开摄像头。请检查权限设置。")
        return

    print("摄像头已启动。按 'q' 键退出程序。")

    # 3. 循环处理每一帧
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法接收帧 (stream end?). Exiting ...")
            break

        # 4. 模型推理
        # stream=True 会让推理更流畅，verbose=False 减少终端打印
        # conf=0.5 是置信度阈值，你可以根据需要调整
        results = model(frame, stream=True, verbose=False, conf=0.5)

        # 5. 在帧上绘制结果
        # results 是一个生成器，我们需要遍历它
        for result in results:
            # plot() 方法会将检测框画在图像上
            annotated_frame = result.plot()
            
            # 显示图像
            cv2.imshow("YOLOv9e PPE Detection", annotated_frame)

        # 6. 按 'q' 退出
        if cv2.waitKey(1) == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_ppe_detection()