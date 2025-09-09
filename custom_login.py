import streamlit as st
import streamlit.components.v1 as components
from auth_utils import init_supabase_client, sign_in, sign_up, sign_in_with_google, send_password_reset_email

def render_custom_login():
    """
    커스텀 HTML 로그인 페이지를 Streamlit에 렌더링하고 인증 처리
    """
    
    # Supabase 클라이언트 초기화
    supabase = init_supabase_client()
    
    # HTML 템플릿
    login_html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>교실의 온도 - 로그인</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
            body {
                font-family: 'Inter', sans-serif;
            }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
        <div class="w-full max-w-md">
            <!-- 메인 컨테이너 -->
            <div class="bg-white rounded-lg shadow-xl border-t-4 border-red-600 overflow-hidden">
                <!-- 헤더 영역 -->
                <div class="px-8 pt-8 pb-6">
                    <!-- 제목과 아이콘 -->
                    <div class="text-center mb-4">
                        <div class="flex items-center justify-center gap-3 mb-3">
                            <h1 class="text-3xl font-black text-gray-900">교실의 온도</h1>
                            <!-- 온도계 아이콘 -->
                            <div class="w-8 h-8 flex items-center justify-center">
                                <svg class="w-6 h-6 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M15 13V5a3 3 0 0 0-6 0v8a5 5 0 1 0 6 0zM12 4a1 1 0 0 1 1 1v8.26a3 3 0 1 1-2 0V5a1 1 0 0 1 1-1z"/>
                                </svg>
                            </div>
                        </div>
                        <!-- 강조선 -->
                        <div class="w-10 h-1 bg-red-600 mx-auto rounded-full"></div>
                    </div>
                    
                    <!-- 탭 메뉴 -->
                    <div class="flex justify-center mb-6">
                        <div class="flex space-x-8">
                            <button id="loginTab" class="tab-button active px-4 py-2 font-semibold text-red-600 border-b-2 border-red-600 transition-colors">
                                로그인
                            </button>
                            <button id="signupTab" class="tab-button px-4 py-2 font-semibold text-gray-500 border-b-2 border-transparent hover:text-gray-700 transition-colors">
                                회원가입
                            </button>
                        </div>
                    </div>
                    
                    <!-- 구분선 -->
                    <hr class="border-gray-200 mb-6">
                    
                    <!-- 로그인 폼 -->
                    <div id="loginForm">
                        <div class="space-y-5">
                            <!-- 이메일 입력 -->
                            <div>
                                <label for="loginEmail" class="block text-sm font-semibold text-gray-700 mb-2">
                                    이메일
                                </label>
                                <input 
                                    type="email" 
                                    id="loginEmail" 
                                    placeholder="이메일 주소를 입력하세요"
                                    class="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                    required
                                >
                            </div>
                            
                            <!-- 비밀번호 입력 -->
                            <div>
                                <label for="loginPassword" class="block text-sm font-semibold text-gray-700 mb-2">
                                    비밀번호
                                </label>
                                <div class="relative">
                                    <input 
                                        type="password" 
                                        id="loginPassword" 
                                        placeholder="비밀번호를 입력하세요"
                                        class="w-full px-4 py-3 pr-12 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                        required
                                    >
                                    <!-- 비밀번호 보기/숨기기 버튼 -->
                                    <button 
                                        type="button" 
                                        class="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-400 hover:text-gray-600"
                                        onclick="togglePassword('loginPassword', 'loginEyeIcon')"
                                    >
                                        <i id="loginEyeIcon" class="fas fa-eye text-lg"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- 로그인 버튼 -->
                            <button 
                                type="button"
                                onclick="handleLogin()"
                                class="w-full bg-white text-gray-700 font-semibold py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
                            >
                                로그인
                            </button>
                        </div>
                        
                        <!-- OR 구분선 -->
                        <div class="relative my-6">
                            <div class="absolute inset-0 flex items-center">
                                <div class="w-full border-t border-gray-300"></div>
                            </div>
                            <div class="relative flex justify-center text-sm">
                                <span class="px-2 bg-white text-gray-500 font-medium">OR</span>
                            </div>
                        </div>
                        
                        <!-- Google 로그인 버튼 -->
                        <button onclick="handleGoogleLogin()" class="w-full bg-white text-gray-700 font-semibold py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 flex items-center justify-center gap-3">
                            <svg class="w-5 h-5" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                            </svg>
                            Google로 로그인
                        </button>
                        
                        <!-- 비밀번호 찾기 -->
                        <div class="text-center mt-6">
                            <button onclick="showPasswordReset()" class="text-sm text-gray-500 hover:text-red-600 transition-colors">
                                비밀번호를 잊으셨나요?
                            </button>
                        </div>
                    </div>
                    
                    <!-- 회원가입 폼 (처음에는 숨겨짐) -->
                    <div id="signupForm" style="display: none;">
                        <div class="space-y-5">
                            <!-- 이메일 입력 -->
                            <div>
                                <label for="signupEmail" class="block text-sm font-semibold text-gray-700 mb-2">
                                    이메일
                                </label>
                                <input 
                                    type="email" 
                                    id="signupEmail" 
                                    placeholder="이메일 주소를 입력하세요"
                                    class="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                    required
                                >
                            </div>
                            
                            <!-- 비밀번호 입력 -->
                            <div>
                                <label for="signupPassword" class="block text-sm font-semibold text-gray-700 mb-2">
                                    비밀번호
                                </label>
                                <div class="relative">
                                    <input 
                                        type="password" 
                                        id="signupPassword" 
                                        placeholder="비밀번호를 입력하세요 (6자 이상)"
                                        class="w-full px-4 py-3 pr-12 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                        required
                                    >
                                    <button 
                                        type="button" 
                                        class="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-400 hover:text-gray-600"
                                        onclick="togglePassword('signupPassword', 'signupEyeIcon')"
                                    >
                                        <i id="signupEyeIcon" class="fas fa-eye text-lg"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- 비밀번호 확인 -->
                            <div>
                                <label for="signupPasswordConfirm" class="block text-sm font-semibold text-gray-700 mb-2">
                                    비밀번호 확인
                                </label>
                                <div class="relative">
                                    <input 
                                        type="password" 
                                        id="signupPasswordConfirm" 
                                        placeholder="비밀번호를 다시 입력하세요"
                                        class="w-full px-4 py-3 pr-12 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                        required
                                    >
                                    <button 
                                        type="button" 
                                        class="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-400 hover:text-gray-600"
                                        onclick="togglePassword('signupPasswordConfirm', 'confirmEyeIcon')"
                                    >
                                        <i id="confirmEyeIcon" class="fas fa-eye text-lg"></i>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- 회원가입 버튼 -->
                            <button 
                                type="button"
                                onclick="handleSignup()"
                                class="w-full bg-white text-gray-700 font-semibold py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
                            >
                                회원가입
                            </button>
                        </div>
                    </div>
                    
                    <!-- 비밀번호 재설정 폼 (처음에는 숨겨짐) -->
                    <div id="passwordResetForm" style="display: none;">
                        <div class="space-y-5">
                            <div>
                                <label for="resetEmail" class="block text-sm font-semibold text-gray-700 mb-2">
                                    가입한 이메일 주소
                                </label>
                                <input 
                                    type="email" 
                                    id="resetEmail" 
                                    placeholder="이메일 주소를 입력하세요"
                                    class="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all duration-200"
                                    required
                                >
                            </div>
                            
                            <button 
                                type="button"
                                onclick="handlePasswordReset()"
                                class="w-full bg-white text-gray-700 font-semibold py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
                            >
                                재설정 링크 보내기
                            </button>
                            
                            <button 
                                type="button"
                                onclick="showLogin()"
                                class="w-full text-gray-500 hover:text-red-600 text-sm font-medium transition-colors"
                            >
                                로그인으로 돌아가기
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // 메시지 표시 함수
            function showMessage(message, type) {
                // Streamlit과 통신하기 위해 window.parent에 메시지 전송
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    message: message,
                    messageType: type
                }, '*');
            }

            // 비밀번호 보기/숨기기 기능
            function togglePassword(inputId, iconId) {
                const passwordInput = document.getElementById(inputId);
                const eyeIcon = document.getElementById(iconId);
                
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    eyeIcon.classList.remove('fa-eye');
                    eyeIcon.classList.add('fa-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    eyeIcon.classList.remove('fa-eye-slash');
                    eyeIcon.classList.add('fa-eye');
                }
            }

            // 탭 전환 기능
            function showLogin() {
                document.getElementById('loginForm').style.display = 'block';
                document.getElementById('signupForm').style.display = 'none';
                document.getElementById('passwordResetForm').style.display = 'none';
                
                // 탭 활성화 상태 변경
                document.getElementById('loginTab').classList.add('active', 'text-red-600', 'border-red-600');
                document.getElementById('loginTab').classList.remove('text-gray-500', 'border-transparent');
                document.getElementById('signupTab').classList.remove('active', 'text-red-600', 'border-red-600');
                document.getElementById('signupTab').classList.add('text-gray-500', 'border-transparent');
            }
            
            function showSignup() {
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('signupForm').style.display = 'block';
                document.getElementById('passwordResetForm').style.display = 'none';
                
                // 탭 활성화 상태 변경
                document.getElementById('signupTab').classList.add('active', 'text-red-600', 'border-red-600');
                document.getElementById('signupTab').classList.remove('text-gray-500', 'border-transparent');
                document.getElementById('loginTab').classList.remove('active', 'text-red-600', 'border-red-600');
                document.getElementById('loginTab').classList.add('text-gray-500', 'border-transparent');
            }
            
            function showPasswordReset() {
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('signupForm').style.display = 'none';
                document.getElementById('passwordResetForm').style.display = 'block';
            }

            // 이벤트 리스너 추가
            document.getElementById('loginTab').addEventListener('click', showLogin);
            document.getElementById('signupTab').addEventListener('click', showSignup);

            // 로그인 처리
            function handleLogin() {
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPassword').value;
                
                if (!email || !password) {
                    showMessage('이메일과 비밀번호를 입력해주세요.', 'error');
                    return;
                }
                
                // Streamlit으로 로그인 데이터 전송
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    action: 'login',
                    email: email,
                    password: password
                }, '*');
            }

            // 회원가입 처리
            function handleSignup() {
                const email = document.getElementById('signupEmail').value;
                const password = document.getElementById('signupPassword').value;
                const confirmPassword = document.getElementById('signupPasswordConfirm').value;
                
                if (!email || !password || !confirmPassword) {
                    showMessage('모든 필드를 입력해주세요.', 'error');
                    return;
                }
                
                if (password !== confirmPassword) {
                    showMessage('비밀번호가 일치하지 않습니다.', 'error');
                    return;
                }
                
                // Streamlit으로 회원가입 데이터 전송
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    action: 'signup',
                    email: email,
                    password: password
                }, '*');
            }

            // 구글 로그인 처리
            function handleGoogleLogin() {
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    action: 'google_login'
                }, '*');
            }

            // 비밀번호 재설정 처리
            function handlePasswordReset() {
                const email = document.getElementById('resetEmail').value;
                
                if (!email) {
                    showMessage('이메일을 입력해주세요.', 'error');
                    return;
                }
                
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    action: 'password_reset',
                    email: email
                }, '*');
            }
        </script>
    </body>
    </html>
    """
    
    # HTML 컴포넌트 렌더링 및 사용자 입력 받기
    result = components.html(login_html, height=800, scrolling=True)
    
    # 컴포넌트에서 데이터가 전송되면 처리
    if result:
        action = result.get('action')
        
        if action == 'login':
            email = result.get('email')
            password = result.get('password')
            status, message = sign_in(supabase, email, password)
            
            if status == "success":
                st.success(message)
                st.rerun()
            else:
                st.error(message)
                
        elif action == 'signup':
            email = result.get('email')
            password = result.get('password')
            status, message = sign_up(supabase, email, password)
            
            if status == "success":
                st.success(message)
            else:
                st.error(message)
                
        elif action == 'google_login':
            sign_in_with_google(supabase)
            
        elif action == 'password_reset':
            email = result.get('email')
            status, message = send_password_reset_email(supabase, email)
            
            if status == "success":
                st.success(message)
            else:
                st.error(message)

    return result