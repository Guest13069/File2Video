import cv2
import numpy as np
import os
import imageio
import shutil

directory = ""
output_directory = ""
width = 1920
height = 1080
pixel_size = 4
num_bytes = ((width // pixel_size) * (height // pixel_size)) // 4
end_file = False
num_png = 0
frames_per_image = 1
outfile_ext = ".mp4"
tolerance = 150


def main():
    user_input = input("Do you want to encode (e) or decode(d) or both (b): ")
    file_to_convert = input("Enter the file to convert: ")

    if user_input == 'e':
        encode(file_to_convert)
    elif user_input == 'd':
        decode(file_to_convert)
    elif user_input == 'b':
        encode(file_to_convert)
        decode(file_to_convert)
    else:
        print("Invalid input")


def generate_png(image, output_name):
    output_path = os.path.join(directory, output_name)
    imageio.imwrite(output_path, image)


def generate_image_array(bytes):
    image = np.zeros((width, height, 4), dtype=np.uint8)
    grid_pos = 0

    for y in range(height):
        for x in range(width):
            pixel_index = (y * width + x) * 4
            grid_pos = (x // pixel_size) + (width // pixel_size) * (y // pixel_size)

            bits = 0
            if grid_pos // 4 < len(bytes):
                bits = (bytes[grid_pos // 4] >> (6 - ((grid_pos % 4) * 2))) & 3
                image[pixel_index:pixel_index + 4] = [0, 0, 0, 255] if bits == 0 else \
                                                       [255, 0, 0, 255] if bits == 1 else \
                                                       [0, 255, 0, 255] if bits == 2 else \
                                                       [0, 0, 255, 255]

            else:
                image[pixel_index:pixel_index + 4] = [255, 255, 255, 255]

    return image.flatten()


def get_nth_set(n, file_name):
    global end_file
    bytes_to_use = num_bytes
    result = []

    with open(file_name, 'rb') as file:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(n * bytes_to_use, os.SEEK_SET)

        if n * bytes_to_use + bytes_to_use > file_size:
            bytes_to_use = file_size - n * bytes_to_use
            end_file = True

        buffer = file.read(bytes_to_use)
        result.extend(buffer)

    return result


def generate_video():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter("output.mp4", fourcc, 30, (width, height))

    if not video.isOpened():
        print(f"Failed to create video file: output.mp4")
        return

    for i in range(num_png):
        image_path = os.path.join(directory, f"{i}.png")
        frame = cv2.imread(image_path)

        if frame is None:
            break

        for _ in range(frames_per_image):
            video.write(frame)

    video.release()
    print(f"Video created successfully: output.mp4")


def encode(file_to_encode):
    global num_png, end_file
    bytes_ = []

    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(directory)

    while not end_file:
        output_name = f"{num_png}.png"
        bytes_ = get_nth_set(num_png, file_to_encode)
        image = generate_image_array(bytes_)
        generate_png(image.reshape((height, width, 4)), output_name)
        num_png += 1

    print(f"{num_png} images saved")
    generate_video()


def decode(file_to_decode):
    global num_png
    bytes_ = []
    shutil.rmtree(output_directory, ignore_errors=True)
    generate_png_sequence(file_to_decode)
    os.remove("outfile" + outfile_ext)

    for i in range(num_png):
        pic_name = os.path.join(output_directory, f"{i}.png")
        bytes_ = png_to_data(pic_name)
        append_bytes_to_file(bytes_, "outfile" + outfile_ext)


def generate_png_sequence(video_path):
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print(f"Error opening video file: {video_path}")
        return

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 0

    os.makedirs(output_directory, exist_ok=True)

    while frame_number < frame_count:
        ret, frame = video.read()

        if not ret:
            print(f"Error reading frame {frame_number} from video.")
            break

        output_name = os.path.join(output_directory, f"{frame_number}.png")
        if not cv2.imwrite(output_name, frame):
            print(f"Error saving frame {frame_number} as PNG.")

        frame_number += 1

    video.release()
    print(f"PNG sequence generated successfully. Total frames: {frame_number}")
    global num_png
    num_png = frame_number


def png_to_data(png_image_path):
    bytes_ = []
    byte = 0
    image = cv2.imread(png_image_path)

    if image is None:
        print(f"Error reading image: {png_image_path}")
        return bytes_

    for y in range(pixel_size // 2, image.shape[0], pixel_size):
        for x in range(pixel_size // 2, image.shape[1], pixel_size):
            color = image[y, x]
            byte = byte << 2

            if all(c > tolerance for c in color):
                return bytes_

            if color[2] > tolerance:
                byte |= 1
            elif color[0] > tolerance:
                byte |= 3
            elif color[1] > tolerance:
                byte |= 2

            bytes_.append(byte)
            byte = 0

    return bytes_


def append_bytes_to_file(bytes_, filename):
    with open(filename, 'ab') as file:
        file.write(bytes_)


if __name__ == "__main__":
    main()
