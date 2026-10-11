import os
import asyncio
from flask import Flask, render_template, request, jsonify, send_file
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, vfx

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# edge-tts ဖြင့် မြန်မာအသံထုတ်ယူရန် အဓိက လုပ်ဆောင်ချက်
async def text_to_speech(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    try:
        # Frontend က ပို့လိုက်သော အချက်အလက်များကို လက်ခံခြင်း
        video_file = request.files.get('video')
        prompt = request.form.get('prompt', '')
        genre = request.form.get('genre', 'Thriller')
        tone = request.form.get('tone', 'Suspenseful')
        voice = request.form.get('voice', 'my-MM-NilarNeural')
        ratio = request.form.get('ratio', '9:16')
        auto_color = request.form.get('auto_color') == 'true'

        if not video_file:
            return jsonify({'error': 'ဗီဒီယိုဖိုင် မပါရှိပါ။'}), 400

        # ဗီဒီယိုဖိုင် သိမ်းဆည်းရန်
        video_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
        video_file.save(video_path)

        # Recap Script ဖန်တီးခြင်း (Prompt & Genre အပေါ်မူတည်၍)
        script_text = f"ဒီဇာတ်လမ်းလေးကတော့ {genre} အမျိုးအစားဖြစ်ပြီး၊ {prompt} ကို စိတ်လှုပ်ရှားဖွယ် ဇာတ်ကြောင်းပြောပြသွားမှာ ဖြစ်ပါတယ်။"

        # edge-tts ဖြင့် အသံဖိုင်ထုတ်ယူခြင်း
        audio_path = os.path.join(OUTPUT_FOLDER, 'generated_voice.mp3')
        asyncio.run(text_to_speech(script_text, voice, audio_path))

        # Moviepy ဖြင့် ဗီဒီယိုနှင့် အသံပေါင်းစပ်ခြင်း၊ Ratio နှင့် Color ချိန်ညှိခြင်း
        clip = VideoFileClip(video_path)
        
        # Ratio ချိန်ညှိခြင်း (TikTok အတွက် 9:16 သို့မဟုတ် YouTube အတွက် 16:9)
        if ratio == '9:16':
            w, h = clip.size
            target_w = int(h * 9 / 16)
            if w > target_w:
                x1 = (w - target_w) / 2
                clip = clip.crop(x1=x1, y1=0, x2=x1 + target_w, y2=h)
        
        # Auto Color Grading (အရောင်အသွေး မြှင့်တင်ခြင်း)
        if auto_color:
            clip = clip.fx(vfx.colorx, 1.2)

        # အသံဖိုင်ထည့်သွင်းခြင်း
        audio = AudioFileClip(audio_path)
        final_clip = clip.set_audio(audio)

        # ရလဒ်ဗီဒီယို ထုတ်ယူခြင်း
        output_video_path = os.path.join(OUTPUT_FOLDER, 'final_recap.mp4')
        final_clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac', fps=24)

        return jsonify({
            'success': True,
            'message': 'ဗီဒီယိုနှင့် AI အသံ ပေါင်းစပ်ပြီးပါပြီ!',
            'download_url': '/download'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download_file():
    output_video_path = os.path.join(OUTPUT_FOLDER, 'final_recap.mp4')
    return send_file(output_video_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
