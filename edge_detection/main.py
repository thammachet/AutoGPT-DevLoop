import cv2

def main():
    # Open default camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    # Create windows
    cv2.namedWindow('Original')
    cv2.namedWindow('Edges')

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Detect edges using Canny
        edges = cv2.Canny(gray, 100, 200)

        # Display the resulting frames
        cv2.imshow('Original', frame)
        cv2.imshow('Edges', edges)

        # Break loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture and destroy windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()