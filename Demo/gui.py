import tkinter as tk
from PIL import ImageTk, Image
import mysql.connector
import torch
import read_plate
import process_image
import cv2 
import datetime
import torch
import mysql.connector
class ParkingManagementGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Parking System Management")
        self.btn_capture = tk.Button(self.window, text="Take Photo",font=("Arial", 12), command=self.capture_image)

        self.license_plate_label = tk.Label(self.window, text="Plate Number:",font=("Arial", 12))
        self.license_plate_entry = tk.Entry(self.window,width=20)
        self.btn_save_license_plate = tk.Button(self.window, text="Save",font=("Arial", 12), command=self.save_license_plate)
        
        self.transport_status_announcement = tk.Label(self.window, text="",font=("Arial", 12))
        self.total_money_announcement =tk.Label(self.window, text="",font=("Arial", 12))

        self.camera_frame = tk.Frame(self.window)
        self.camera_label = tk.Label(self.camera_frame)

        self.captured_image_frame = tk.Frame(self.window)
        self.captured_image_label = tk.Label(self.captured_image_frame)

        self.camera = cv2.VideoCapture(0)
        self.update_camera()


        self.btn_capture.pack(side=tk.TOP)
        self.license_plate_label.pack(side=tk.TOP)
        self.license_plate_entry.pack(side=tk.TOP)
        self.btn_save_license_plate.pack(side=tk.TOP)
        self.transport_status_announcement.pack(side=tk.TOP)
        self.total_money_announcement.pack(side=tk.TOP)
        self.camera_frame.pack(side=tk.LEFT)
        self.camera_label.pack(side=tk.LEFT)
        self.captured_image_frame.pack(side=tk.RIGHT)
        self.captured_image_label.pack(side=tk.RIGHT)

  
    def caculate_fee(self):
        number_plate = self.license_plate_entry.get()
        con = self.connectDB()
        cursor = con.cursor()
        sql = "SELECT * FROM Numberplate WHERE number_plate = %s ORDER BY date_in DESC LIMIT 1"
        cursor.execute(sql,(number_plate,))
        result = cursor.fetchone()
        con.close()
        cursor.close()
        if(str(result[4]) != "Null"):        
            time_diff = result[4]-result[3]
            hours = (time_diff.total_seconds())/3600
        total_fee = round(hours*1000,2)
        announce = "Fee Payment : "+str(total_fee) +"VND"
        return announce


    def capture_image(self):
        _, frame = self.camera.read()
        license_plate_detection_model = torch.hub.load('Model/Model_YOLOv7', 'custom','Model/Model_YOLOv7/runs/train/exp/pl_det/pl_det.pt',force_reload =True,source='local')
        plates = (license_plate_detection_model(frame, size=640).pandas().xyxy[0].values.tolist())
        if len(plates) ==0:
            cv2.putText(frame, " No plate in this image",(0,100),cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 2)
            self.display_image(self.captured_image_label, frame)
        else:
            plate = plates[0]
            x = int(plate[0]) 
            y = int(plate[1])
            w = int(plate[2] - plate[0]) 
            h = int(plate[3] - plate[1])
            number_plate = frame[y:y + h, x:x + w]
            cv2.imwrite("Demo/images/numberplate.jpg",number_plate)
            self.display_numberplate_Entry()
            self.display_image(self.captured_image_label, number_plate)
    

    def save_license_plate(self):
        number_plate = self.license_plate_entry.get()
        if(number_plate != "unknown"):
            check = self.checkNp(number_plate)
            if (check == 0):
                self.insertNp(number_plate)
            else:
                check2 = self.checkNpStatus(number_plate)
                if (check2[2] == 1):
                    self.updateNp(check2[0])
                    text = self.caculate_fee()
                    self.total_money_announcement.config(text=text)
                else:
                    self.insertNp(number_plate)
        else:
            pass
    def display_image(self, label, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(image_rgb)
        img = img.resize((640, 480), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label.configure(image=photo)
        label.image = photo

    def display_numberplate_Entry(self):
        result = self.readnumberplate()
        self.license_plate_entry.delete(0, tk.END)
        self.license_plate_entry.insert(0, str(result))

    def update_camera(self):
        ret, frame = self.camera.read()
        self.display_image(self.camera_label, frame)
        self.window.after(10, self.update_camera)
    
    def connectDB(self):
        conn = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'pythonAI'
        )
        return conn

    
    def checkNp(self,number_plate):
        con = self.connectDB()
        cursor = con.cursor()
        sql = "SELECT * FROM Numberplate WHERE number_plate = %s"
        cursor.execute(sql,(number_plate,))
        cursor.fetchall()
        result = cursor._rowcount
        con.close()
        cursor.close()
        return result

    def checkNpStatus(self,number_plate):
        con = self.connectDB()
        cursor = con.cursor()
        sql = "SELECT * FROM Numberplate WHERE number_plate = %s ORDER BY date_in DESC LIMIT 1"
        cursor.execute(sql,(number_plate,))
        result = cursor.fetchone()
        con.close()
        cursor.close()
        return result
    # Tạo bản ghi dành cho xe vào bãi gửi xe (Cho xe vào bãi)
    # Trường hợp 1 : Tên biển số xe đọc từ ảnh chưa tồn tại trong database 
    # Trường hợp 2 : Tên biển số xe đọc từ ảnh đã tồn tại trong database nhưng trạng thái của bản ghi gần nhất là 0 (đã từng gửi nhưng lấy ra khỏi bãi xe rồi) 
    def insertNp(self, number_plate):
        con = self.connectDB()
        cursor = con.cursor()
        sql = "INSERT INTO Numberplate(number_plate,status,date_in) VALUES(%s,%s,%s)"
        now = datetime.datetime.now()
        date_in = now.strftime("%Y/%m/%d %H:%M:%S")
        self.transport_status_announcement.config(text= "Come in at "+str(date_in))
        cursor.execute(sql,(number_plate,'0',date_in))
        con.commit()
        cursor.close()
        con.close()

    def updateNp(self, Id):
        con = self.connectDB()
        cursor = con.cursor()
        sql = "UPDATE Numberplate SET status = 0, date_out = %s WHERE Id = %s"
        now = datetime.datetime.now()
        date_out = now.strftime("%Y/%m/%d %H:%M:%S")
        self.transport_status_announcement.config(text= "Come out at "+str(date_out))
        cursor.execute(sql,(date_out,Id))
        con.commit()
        cursor.close()
        con.close()

    def readnumberplate(self):
        character_recognition_model = torch.hub.load('D:/Course_FPT/Term_7/DPL301/Project/Model/Model_YOLOv7', 'custom','D:/Course_FPT/Term_7/DPL301/Project/Model/Model_YOLOv7/runs/train/exp/ocr/ocr.pt',force_reload =True,source='local')
        image_path = "D:/AI-ComputerVision/Personal_Project/University_Transport_Management_Project/Project/Demo/images/numberplate.jpg"
        character_recognition_model.conf = 0.7
        img = cv2.imread(image_path)
        number_plate = ""
        flag=0
        for is_change_constrast in range(0,2):
            for is_center_limit in range(0,2):
                number_plate = read_plate.read_plate(character_recognition_model,process_image.deskew(img,is_change_constrast,is_center_limit))
                if number_plate != "unknown":
                    flag =1
                if(flag==1):
                    break
        return number_plate
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    gui = ParkingManagementGUI()
    gui.run()