import os
import re
import shutil
import psutil
import logging
import ctypes
import sys
import tkinter as tk
from tkinter import messagebox

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cleanup.log', mode='w'),  # Перезапись файла при каждом запуске
            logging.StreamHandler()
        ]
    )

def show_popup(message, error = 0):
    root = tk.Tk()
    root.withdraw()  # Скрываем основное окно
    if error == 1:
        messagebox.showerror("Ошибка", message)
    else:
        messagebox.showinfo("Информация", message)
    root.destroy()

def delete_uuid_folders(directory):
    if not os.path.exists(directory):
        logging.warning(f"Директория {directory} не существует.")
        return

    logging.info(f"Обработка директории: {directory}")
    uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            if uuid_pattern.match(dir_name):
                dir_path = os.path.join(root, dir_name)
                logging.info(f"Удаление папки: {dir_path}")
                try:
                    shutil.rmtree(dir_path)
                except Exception as e:
                    logging.error(f"Не удалось удалить {dir_path}. Причина: {e}")

def clean_temp_folder(temp_dir):
    logging.info(f"Очистка папки Temp: {temp_dir}")
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.error(f"Не удалось удалить {file_path}. Причина: {e}")

def main():
    if not is_admin():
        show_popup("Для выполнения этого скрипта требуются права администратора.", error = 1)
        logging.error("Скрипт не запущен с правами администратора.")
        sys.exit(1)
        
    if is_1c_client_running(): 
        show_popup("Перед выполнением чистки необходимо закрыть все экземпляры 1С", error = 1)
        logging.error("Обнаружен открытый экземпляр 1С")
        sys.exit(1)

    setup_logging()

    local_app_data = os.path.join(os.getenv('LOCALAPPDATA'), '1C', '1Cv8')
    app_data = os.path.join(os.getenv('APPDATA'), '1C', '1Cv8')
    temp_dir = os.getenv('TEMP')

    delete_uuid_folders(local_app_data)
    delete_uuid_folders(app_data)
    clean_temp_folder(temp_dir)

    logging.info("Операция завершена.")
    show_popup("Операция завершена. Логи записаны в файл cleanup.log.")

if __name__ == "__main__":
    main()
