from matplotlib.patches import Circle
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import numpy as np
import os

class PoseNet():
	def __init__(self, run_on_pi=True):

		self.model_path = "posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite"
		
		if os.path.exists(self.model_path):
			print("Model exist...")
		else:
			print("Downloading model...")
			os.system("wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/posenet_mobilenet_v1_100_257x257_multi_kpt_stripped.tflite")

		self.run_on_pi = run_on_pi

		if run_on_pi:
			import tflite_runtime.interpreter as tflite
			self.interpreter = tflite.Interpreter(model_path=self.model_path)
		else:
			import tensorflow as tf
			self.interpreter = tf.lite.Interpreter(model_path=self.model_path)


		self.interpreter.allocate_tensors()
		self.input_details = self.interpreter.get_input_details()
		self.output_details = self.interpreter.get_output_details()

		self.height = self.input_details[0]['shape'][1]
		self.width = self.input_details[0]['shape'][2]


	def parse_output(self, heatmap_data, offset_data, threshold):

		'''
		Input:
			heatmap_data - hetmaps for an image. Three dimension array
			offset_data - offset vectors for an image. Three dimension array
			threshold - probability threshold for the keypoints. Scalar value
		Output:
			array with coordinates of the keypoints and flags (0/1 : 0 - key-point exist &
																	 1 - no key-point exist)
		'''

		joint_num = heatmap_data.shape[-1]
		pose_kps = np.zeros((joint_num,3), np.uint32)

		for i in range(heatmap_data.shape[-1]):

			joint_heatmap = heatmap_data[...,i]
			max_val_pos = np.squeeze(np.argwhere(joint_heatmap==np.max(joint_heatmap)))
			remap_pos = np.array(max_val_pos/8*257,dtype=np.int32)
			pose_kps[i,0] = int(remap_pos[0] + offset_data[max_val_pos[0],max_val_pos[1],i])
			pose_kps[i,1] = int(remap_pos[1] + offset_data[max_val_pos[0],max_val_pos[1],i+joint_num])
			max_prob = np.max(joint_heatmap)

			if max_prob > threshold:
				if pose_kps[i,0] < 257 and pose_kps[i,1] < 257:
					pose_kps[i,2] = 1

		return pose_kps


	def draw_kps(self, show_img, kps, ratio):

		pil_im = Image.fromarray(show_img)
		draw = ImageDraw.Draw(pil_im)

		for i in range(kps.shape[0]):
			if kps[i,2]:
						
				x, y, r  = int(round(kps[i,1]*ratio[1])), int(round(kps[i,0]*ratio[0])), 2
				leftUpPoint = (x-r, y-r)
				rightDownPoint = (x+r, y+r)
				twoPointList = [leftUpPoint, rightDownPoint]
				draw.ellipse(twoPointList, fill=(255,0,0,255))
				
		pil_im.save(self.output_path, "PNG")


	def detection_from_image(self, image_path):

		self.template_path = image_path
		self.output_path = self.template_path.replace("jpg", "png")

		template_image_src = Image.open(self.template_path)
		src_templ_height, src_tepml_width = template_image_src.size 
		template_image = template_image_src.resize((self.width, self.height), Image.ANTIALIAS)

		templ_ratio_width = src_tepml_width/self.width
		templ_ratio_height = src_templ_height/self.height
		

		template_input = np.expand_dims(template_image.copy(), axis=0)
		floating_model = self.input_details[0]['dtype'] == np.float32

		if floating_model:
			template_input = (np.float32(template_input) - 127.5) / 127.5

		self.interpreter.set_tensor(self.input_details[0]['index'], template_input)
		self.interpreter.invoke()

		template_output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
		template_offset_data = self.interpreter.get_tensor(self.output_details[1]['index'])

		template_heatmaps = np.squeeze(template_output_data)
		template_offsets = np.squeeze(template_offset_data)
		
		template_show = np.squeeze((template_input.copy()*127.5+127.5)/255.0)
		template_show = np.array(template_show*255,np.uint8)
		template_kps = self.parse_output(template_heatmaps,template_offsets,0.3)
		print("Key points: ",template_kps)

		tt = np.asarray(template_image_src)
		self.draw_kps(tt,template_kps, (templ_ratio_width, templ_ratio_height))

	
	def detection_from_video(self, video_path=0):

		if self.run_on_pi:
			print("Can't open video")
			return
		
		import cv2

		def process_frame(template_image_src):
			src_tepml_width, src_templ_height, _ = template_image_src.shape 
			template_image = cv2.resize(template_image_src, (self.width, self.height))
			
			templ_ratio_width = src_tepml_width/self.width
			templ_ratio_height = src_templ_height/self.height
			
			template_input = np.expand_dims(template_image.copy(), axis=0)
			floating_model = self.input_details[0]['dtype'] == np.float32
			
			if floating_model:
				template_input = (np.float32(template_input) - 127.5) / 127.5
				
			
			self.interpreter.set_tensor(self.input_details[0]['index'], template_input)
			
			self.interpreter.invoke()
			
			template_output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
			template_offset_data = self.interpreter.get_tensor(self.output_details[1]['index'])
			
			template_heatmaps = np.squeeze(template_output_data)
			template_offsets = np.squeeze(template_offset_data)
			
			
			template_show = np.squeeze((template_input.copy()*127.5+127.5)/255.0)
			template_show = np.array(template_show*255,np.uint8)
			template_kps = self.parse_output(template_heatmaps,template_offsets,0.3)
				
			return draw_kps_cv2(template_image_src.copy(),template_kps, (templ_ratio_width, templ_ratio_height)) 

		def draw_kps_cv2(show_img,kps, ratio):
			for i in range(kps.shape[0]):
				if kps[i,2]:
					cv2.circle(show_img,(int(round(kps[i,1]*ratio[1])),int(round(kps[i,0]*ratio[0]))),2,(0,255,255),round(int(1*ratio[1])))
			return show_img

		vs = cv2.VideoCapture(video_path)
		self.output_path = "output.avi"

		fourcc = cv2.VideoWriter_fourcc(*'XVID')
		out = cv2.VideoWriter(self.output_path, fourcc, 20.0, (640,480))

		while True:
			(grabbed, frame) = vs.read()
			if not grabbed:
				break

			frame = process_frame(frame)
			out.write(frame)
			cv2.imshow('frame',frame)
			if cv2.waitKey(1) & 0xFF == ord('q'):
				break

		vs.release()
		out.release()
		cv2.destroyAllWindows()

		
posenet_model = PoseNet(run_on_pi=False)

# Detect key points from image
posenet_model.detection_from_image("1.jpg")

# Detect key points from video
posenet_model.detection_from_video(video_path='test_input.avi')

# Detect key points from webcam
posenet_model.detection_from_video()




