import PySimpleGUI as sg
import socket
from threading import Thread
import os
import sys
import struct

PORT = 8888
HOST = "0.0.0.0"

window = None

def get_data(folder_name: str):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            num_files = struct.unpack('>i', conn.recv(4))[0]
            print(f"Num files: {num_files}")
            
            success = True
            for i in range(num_files):
                window["-Receiving_Text-"].update(f"Recebendo arquivos... ({i} de {num_files})")
                filename_len = struct.unpack('>i', conn.recv(4))[0]
                filename = conn.recv(filename_len).decode("utf-8")
                print(f"Filename: {filename}")
                data_size = struct.unpack('>i', conn.recv(4))[0]
                print(f"Data size: {data_size}")

                data = b""
                try:
                    while True:
                        BUFFER_SIZE = min(data_size, data_size - len(data))
                        buffer = conn.recv(BUFFER_SIZE)
                        if not buffer:
                            print('Erro ao receber arquivo')
                            conn.sendall(b"NAK")
                            window["-Receiving_Text-"].update(f"Erro ao receber arquivo. Tente novamente. Código de erro: 1")
                            success = False
                            break
                        
                        data += buffer

                        if  len(data) == data_size:
                            break

                        if len(data) >= data_size:
                            window["-Receiving_Text-"].update(f"Erro ao receber arquivo. Tente novamente. Código de erro: 2")
                            print("len(data) >= data_size")
                            conn.sendall(b"NAK")
                            success = False
                            break

                    with open(f"{folder_name}/{filename}", 'w') as f:
                        f.write(data.decode("utf-8"))
                
                    if success:
                        conn.sendall(b"ACK")
                except:
                    conn.sendall(b"NAK")
                    window["-Receiving_Text-"].update(f"Erro ao receber arquivo. Tente novamente. Código de erro: 3")
                    success = False     

            if success:
                window["-Receiving_Text-"].update("Dados recebidos com sucesso!!!")


layout = [[sg.Text("Selecione a pasta de destino"), sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"), sg.FolderBrowse()],
            [sg.Button("Receber arquivos"), sg.Text("", key="-Receiving_Text-")]]

window = sg.Window("Data Collector", layout)

folder_name = None

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        os._exit(0)

    if event == "-FOLDER-":
        folder_name = values["-FOLDER-"]

    if event == "Receber arquivos":
        if folder_name is None or folder_name == "":
            window["-Receiving_Text-"].update("Folder Name cannot be empty!")
            continue

        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)

        get_data_thread = Thread(target=get_data, args=(folder_name,))
        get_data_thread.start()

        window["-Receiving_Text-"].update(f"Waiting at: {IPAddr} (port={PORT})")
        window["Receber arquivos"].update(disabled=True)

window.close()