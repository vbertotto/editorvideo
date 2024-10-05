import streamlit as st
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    vfx,
    AudioFileClip,
)
import tempfile
import os
import numpy as np
from PIL import Image
import atexit

# Função para aplicar filtros
def apply_filter(clip, filter_name):
    if filter_name == "Escala de Cinza":
        return clip.fx(vfx.blackwhite)
    elif filter_name == "Sepia":
        def sepia(frame):
            img = Image.fromarray(frame)
            sepia_filter = Image.new("RGB", img.size)
            pixels = img.load()  # create the pixel map

            for py in range(img.size[1]):
                for px in range(img.size[0]):
                    r, g, b = img.getpixel((px, py))

                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)

                    # Clipping to 255
                    tr = min(255, tr)
                    tg = min(255, tg)
                    tb = min(255, tb)

                    sepia_filter.putpixel((px, py), (tr, tg, tb))
            return np.array(sepia_filter)

        return clip.fl_image(sepia)
    elif filter_name == "Espelhamento Horizontal":
        return clip.fx(vfx.mirror_x)
    else:
        return clip

# Função para ajustar velocidade
def adjust_speed(clip, speed_factor):
    return clip.fx(vfx.speedx, speed_factor)

# Configuração da página
st.set_page_config(page_title="Editor de Vídeo Avançado com Streamlit", layout="wide")

st.title("🎬 Editor de Vídeo Avançado com Streamlit")

# Seção de Upload
st.sidebar.header("1. Faça o Upload do Vídeo")
uploaded_video = st.sidebar.file_uploader(
    "Escolha um arquivo de vídeo", type=["mp4", "avi", "mov", "mkv"]
)

uploaded_audio = st.sidebar.file_uploader(
    "Escolha um arquivo de áudio para a música de fundo (opcional)", type=["mp3", "wav", "aac"]
)

if uploaded_video is not None:
    # Salvar o vídeo temporariamente
    tfile_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile_video.write(uploaded_video.read())
    video_path = tfile_video.name

    # Carregar o vídeo com MoviePy
    clip = VideoFileClip(video_path)
    st.sidebar.write("🎥 Duração do Vídeo:", f"{clip.duration:.2f} segundos")
    st.sidebar.video(video_path)

    # Seção de Edição
    st.sidebar.header("2. Opções de Edição")

    # Corte do vídeo
    st.sidebar.subheader("✂️ Corte do Vídeo")
    start_time = st.sidebar.number_input(
        "⏱️ Tempo Inicial (segundos)", min_value=0.0, max_value=clip.duration, value=0.0, step=0.5
    )
    end_time = st.sidebar.number_input(
        "⏱️ Tempo Final (segundos)", min_value=0.0, max_value=clip.duration, value=clip.duration, step=0.5
    )

    if end_time <= start_time:
        st.sidebar.error("⚠️ O tempo final deve ser maior que o tempo inicial.")

    # Adição de Texto
    st.sidebar.subheader("📝 Adicionar Texto")
    add_text = st.sidebar.checkbox("Adicionar texto ao vídeo")
    if add_text:
        txt = st.sidebar.text_input("Texto a ser adicionado", value="Meu Texto")
        txt_position = st.sidebar.selectbox(
            "📍 Posição do Texto", ["top", "center", "bottom", "left", "right"]
        )
        txt_size = st.sidebar.slider("🔠 Tamanho da Fonte", min_value=10, max_value=100, value=50)
        txt_color = st.sidebar.color_picker("🎨 Cor do Texto", "#FFFFFF")
        txt_font = st.sidebar.selectbox(
            "🔤 Fonte do Texto", ["Arial", "Courier", "Liberation-Sans", "Impact"]
        )

    # Aplicação de Filtros
    st.sidebar.subheader("🎨 Aplicar Filtros de Vídeo")
    filter_options = ["Nenhum", "Escala de Cinza", "Sepia", "Espelhamento Horizontal"]
    selected_filter = st.sidebar.selectbox("Escolha um filtro", filter_options)

    # Ajuste de Velocidade
    st.sidebar.subheader("⚡ Ajuste de Velocidade de Reprodução")
    speed_factor = st.sidebar.slider(
        "Fator de Velocidade", min_value=0.5, max_value=2.0, value=1.0, step=0.1
    )

    # Adição de Música de Fundo
    st.sidebar.subheader("🎵 Adicionar Música de Fundo")
    add_music = st.sidebar.checkbox("Adicionar música de fundo")
    if add_music and uploaded_audio is not None:
        # Salvar o áudio temporariamente
        tfile_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tfile_audio.write(uploaded_audio.read())
        audio_path = tfile_audio.name
    elif add_music and uploaded_audio is None:
        st.sidebar.warning("⚠️ Por favor, faça upload de um arquivo de áudio.")

    # Botão para Processar
    if st.sidebar.button("🚀 Processar Vídeo"):
        with st.spinner("Processando o vídeo..."):
            try:
                # Aplicar corte
                edited_clip = clip.subclip(start_time, end_time)

                # Aplicar filtro
                if selected_filter != "Nenhum":
                    edited_clip = apply_filter(edited_clip, selected_filter)

                # Ajustar velocidade
                if speed_factor != 1.0:
                    edited_clip = adjust_speed(edited_clip, speed_factor)

                # Adicionar texto
                if add_text:
                    txt_clip = TextClip(
                        txt,
                        fontsize=txt_size,
                        color=txt_color,
                        font=txt_font,
                        method="caption",
                        size=(edited_clip.w * 0.8, None),
                    )
                    txt_clip = txt_clip.set_position(txt_position).set_duration(edited_clip.duration)
                    edited_clip = CompositeVideoClip([edited_clip, txt_clip])

                # Adicionar música de fundo
                if add_music and uploaded_audio is not None:
                    audio_clip = AudioFileClip(audio_path)
                    # Ajustar a duração da música para coincidir com o vídeo
                    audio_clip = audio_clip.subclip(0, edited_clip.duration)
                    # Ajustar o volume da música
                    audio_clip = audio_clip.volumex(0.5)
                    # Definir a trilha sonora do vídeo
                    edited_clip = edited_clip.set_audio(audio_clip)

                # Salvar o vídeo editado em um arquivo temporário
                output_path = os.path.join(tempfile.gettempdir(), "edited_video.mp4")
                edited_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4)

                # Fechar os clipes para liberar recursos
                edited_clip.close()
                clip.close()
                if add_music and uploaded_audio is not None:
                    audio_clip.close()

                st.success("✅ Vídeo Processado com Sucesso!")

                # Exibir o vídeo editado
                st.video(output_path)

                # Botão para download
                with open(output_path, "rb") as file:
                    btn = st.download_button(
                        label="📥 Baixar Vídeo Editado",
                        data=file,
                        file_name="edited_video.mp4",
                        mime="video/mp4",
                    )

            except Exception as e:
                st.error(f"❌ Ocorreu um erro durante o processamento: {e}")

    # Limpeza de arquivos temporários ao finalizar
    def cleanup():
        try:
            os.remove(video_path)
        except Exception:
            pass
        try:
            if add_music and uploaded_audio is not None:
                os.remove(audio_path)
        except Exception:
            pass
        try:
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
        except Exception:
            pass

    atexit.register(cleanup)

    # Exibição das opções de edição
    st.header("📋 Configurações de Edição")
    st.markdown("Utilize a barra lateral para configurar as edições do seu vídeo.")

    # Visualização das edições selecionadas
    if st.sidebar.button("🔍 Ver Configurações"):
        st.subheader("Configurações Selecionadas")
        st.write("**Corte do Vídeo:**")
        st.write(f"⏱️ Início: {start_time} segundos")
        st.write(f"⏱️ Fim: {end_time} segundos")
        st.write("**Texto Adicionado:**" if add_text else "Texto Adicionado: Não")
        if add_text:
            st.write(f"📝 Texto: {txt}")
            st.write(f"📍 Posição: {txt_position}")
            st.write(f"🔠 Tamanho da Fonte: {txt_size}")
            st.write(f"🎨 Cor do Texto: {txt_color}")
            st.write(f"🔤 Fonte do Texto: {txt_font}")
        st.write("**Filtro Aplicado:**", selected_filter)
        st.write("**Velocidade de Reprodução:**", f"{speed_factor}x")
        st.write("**Música de Fundo Adicionada:**", "Sim" if add_music and uploaded_audio else "Não")

else:
    st.info("🔄 Por favor, faça o upload de um vídeo para começar a editar.")
