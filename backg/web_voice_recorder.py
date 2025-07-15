import requests
import json
import base64
import sounddevice as sd
import numpy as np
import threading
import time

API_KEY = "rDBlDmdDGFfI2FQLO8J14979"
SECRET_KEY = "IKAvhjWnhiiKNOpPAtU2e6fsQrzv6Oqk"

class WebVoiceRecorder:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        self.stream = None
        self.samplerate = 16000
        self.channels = 1
        self.audio_file = "recorded.pcm"
        
    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))
    
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return {"success": False, "error": "正在录音中"}
        
        try:
            self.is_recording = True
            self.frames = []
            
            print("开始录音...")
            sd.default.samplerate = self.samplerate
            sd.default.channels = self.channels
            
            self.stream = sd.InputStream(dtype='int16', callback=self._audio_callback)
            self.stream.start()
            
            return {"success": True, "message": "录音已开始"}
        except Exception as e:
            self.is_recording = False
            return {"success": False, "error": f"开始录音失败: {str(e)}"}
    
    def _audio_callback(self, indata, frames, time, status):
        """音频数据回调"""
        if self.is_recording:
            self.frames.append(indata.copy())
    
    def stop_recording_and_recognize(self):
        """停止录音并进行语音识别"""
        if not self.is_recording:
            return {"success": False, "error": "当前没有在录音"}
        
        try:
            self.is_recording = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            if not self.frames:
                return {"success": False, "error": "没有录制到音频数据"}
            
            print("录音结束，正在保存...")
            # 合并音频数据
            audio = np.concatenate(self.frames, axis=0)
            audio = audio.flatten().astype(np.int16)
            
            # 保存到文件
            audio.tofile(self.audio_file)
            print("录音已保存，正在识别...")
            
            # 进行语音识别
            return self._recognize_speech()
            
        except Exception as e:
            self.is_recording = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            return {"success": False, "error": f"停止录音失败: {str(e)}"}
    
    def _recognize_speech(self):
        """语音识别"""
        try:
            url = "https://vop.baidu.com/server_api"
            with open(self.audio_file, 'rb') as f:
                speech_data = f.read()
            
            speech_base64 = base64.b64encode(speech_data).decode('utf-8')
            
            payload = json.dumps({
                "format": "pcm",
                "rate": self.samplerate,
                "channel": self.channels,
                "cuid": "QxMdYWTn8BomDX2dbV550p7iHX7ocRpj",
                "token": self.get_access_token(),
                "speech": speech_base64,
                "len": len(speech_data)
            }, ensure_ascii=False)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
            result = response.json()
            
            if "result" in result:
                recognized_text = result["result"][0]
                print(f"识别结果：{recognized_text}")
                return {"success": True, "recognized_text": recognized_text}
            else:
                error_msg = result.get("err_msg", "识别失败")
                print(f"识别失败：{error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            print(f"语音识别异常：{str(e)}")
            return {"success": False, "error": f"语音识别失败: {str(e)}"}
    
    def get_status(self):
        """获取录音状态"""
        return {"is_recording": self.is_recording}

# 全局录音器实例
voice_recorder = WebVoiceRecorder() 