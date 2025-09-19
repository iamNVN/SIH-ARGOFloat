import streamlit as st
import httpx
import asyncio
import time
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import uuid
from datetime import datetime
import numpy as np
import base64
import io
import hashlib

class ArgoApp:
    
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        if "server_connected" not in st.session_state:
            st.session_state["server_connected"] = False

        if "tools" not in st.session_state:
            st.session_state["tools"] = []

        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        self.messages = st.session_state["messages"]
        
        # Initialize session state
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False
        if "username" not in st.session_state:
            st.session_state["username"] = ""
        
        # Initialize chats dict and chat counter in session state
        if "chats" not in st.session_state:
            st.session_state["chats"] = {}
        if "chat_counter" not in st.session_state:
            st.session_state["chat_counter"] = 1
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "chats"
        if "map_center" not in st.session_state:
            st.session_state["map_center"] = {"lat": 15.0, "lon": 82.0}
        if "uploaded_files" not in st.session_state:
            st.session_state["uploaded_files"] = []
        if "users_data" not in st.session_state:
            st.session_state["users_data"] = pd.DataFrame({
                'email': ['admin@argo.com', 'analyst@argo.com', 'researcher@argo.com', 
                         'guest@argo.com', 'supervisor@argo.com'],
                'password': ['admin123', 'analyst123', 'research123', 'guest123', 'super123'],
                'status': ['active', 'active', 'inactive', 'active', 'active'],
                'role': ['Administrator', 'User', 'User', 'User', 'Superadmin'],
                'last_login': ['2024-01-15 10:30', '2024-01-15 09:15', '2024-01-10 14:20', 
                              '2024-01-15 11:45', '2024-01-14 16:30']
            })
        
        # Get chat_id from URL or create new
        if st.session_state["authenticated"]:
            query_params = st.query_params
            chat_id = query_params.get("chat_id")
            if not chat_id or chat_id not in st.session_state["chats"]:
                chat_id = str(uuid.uuid4())
                st.session_state["chats"][chat_id] = []
                st.session_state["chat_titles"] = st.session_state.get("chat_titles", {})
                st.session_state["chat_titles"][chat_id] = f"Untitled Chat #{st.session_state['chat_counter']}"
                st.session_state["chat_counter"] += 1
                st.query_params["chat_id"] = chat_id
            self.chat_id = chat_id
            self.messages = st.session_state["chats"][self.chat_id]
            

    def display_message(self, message: Dict[str, Any]):
        if message["role"] == "user" and type(message["content"]) == str:
            st.chat_message("user").write(message["content"])

        # if message["role"] == "assistant" and type(message["content"]) == list:
        #     for item in message["content"]:
        #         if item["type"]=="tool_use":
        #             st.chat_message("assistant").json({
        #                 "tool": item["name"],
        #                 "input": item["input"],
        #             }, expanded=False)

        # if message["role"] == "user" and type(message["content"]) == list:
        #     st.chat_message("assistant").json({
        #         "result": message["content"],
        #     }, expanded=False)
        
        if message["role"] == "assistant" and type(message["content"]) == str:
            st.chat_message("assistant").write(message["content"])

        

    async def get_tools(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_url}/tools")
            return response.json()

    def show_toast(self, message, type="success"):
        """Show toast notification"""
        color = "#28a745" if type == "success" else "#dc3545" if type == "error" else "#ffc107"
        st.markdown(f"""
        <div id="toast" style="
            position: fixed; 
            top: 60px; 
            right: 20px; 
            background: {color}; 
            color: white; 
            padding: 1rem 2rem; 
            border-radius: 0.5rem; 
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        ">
            {message}
        </div>
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        </style>
        <script>
        setTimeout(() => {{
            const toast = document.getElementById('toast');
            if (toast) toast.style.display = 'none';
        }}, 3000);
        </script>
        """, unsafe_allow_html=True)

    def show_modal(self, title, content):
        """Show modal dialog"""
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
        ">
            <div style="
                background: #262730;
                padding: 2rem;
                border-radius: 1rem;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            ">
                <h3 style="margin-top: 0; color: #fff;">{title}</h3>
                <div style="color: #fff; line-height: 1.5;">{content}</div>
                <div style="margin-top: 1.5rem; text-align: right;">
                    <button onclick="this.closest('div[style*=\"position: fixed\"]').style.display='none'" 
                            style="background: #667eea; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.5rem; cursor: pointer;">
                        Close
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def create_dummy_file(self, filename, content_type="text"):
        """Create dummy file content for downloads"""
        if content_type == "csv":
            content = "sensor_id,temperature,salinity,depth,timestamp\n"
            content += "IO-001,26.8,34.2,2500,2024-01-15 10:00:00\n"
            content += "BB-002,28.5,34.7,2600,2024-01-15 10:05:00\n"
            return content.encode('utf-8')
        elif content_type == "json":
            content = '{"sensors": [{"id": "IO-001", "lat": 8.5, "lon": 78.2, "status": "active"}]}'
            return content.encode('utf-8')
        elif content_type == "sql":
            content = "CREATE TABLE argo_data (id INT PRIMARY KEY, sensor_id VARCHAR(10), temperature FLOAT);\n"
            content += "INSERT INTO argo_data VALUES (1, 'IO-001', 26.8);"
            return content.encode('utf-8')
        else:
            return f"Dummy {filename} content generated at {datetime.now()}".encode('utf-8')

    def download_file(self, filename, content, mime_type="text/plain"):
        """Create download link for file"""
        b64 = base64.b64encode(content).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">📥 Download {filename}</a>'
        return href

    def login_page(self):
        """Render centered login page"""
        st.markdown("""
        <style>
        .stVerticalBlock {
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; ">
            <div style="background: white; padding: 2rem; border-radius: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <h1 style="color: #667eea; margin: 0; font-size: 2.5rem;">🌊 ARGO</h1>
                <p style="color: #666; margin-top: 0.5rem;">Ocean Data Analytics Platform</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("### Login")
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            with col2:
                st.markdown('<p style="color: #999; font-size: 0.9rem; margin-top: 0.5rem;">Demo: admin/admin</p>', unsafe_allow_html=True)
            
            if login_btn:
                if username == "admin" and password == "admin":
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    self.show_toast("🎉 Login successful! Welcome to ARGO", "success")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Use admin/admin for demo.")
        

    def setup_custom_css(self):
        """Setup custom CSS for enhanced styling"""
        st.markdown("""
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .css-1d391kg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .chat-message {
            padding: 1rem;
            border-radius: 0.8rem;
            margin-bottom: 1rem;
            display: flex;
            animation: fadeIn 0.3s ease-in;
        }
        
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: 20%;
        }
        
        .assistant-message {
            background: #f8f9fa;
            color: #333;
            margin-right: 20%;
            border-left: 4px solid #667eea;
        }
        
        .status-active {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-inactive {
            color: #dc3545;
            font-weight: bold;
        }
        
        .sensor-card {
            background: #262730;
            padding: 1rem;
            color: #ffffff;
            border-radius: 0.8rem;
            margin: 0.5rem 0;
            border-left: 4px solid #667eea;
        }
        
        .chat-item {
            padding: 0.5rem 0.75rem;
            margin: 0.25rem 0;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: background-color 0.2s;
            border: 1px solid transparent;
            color: rgba(255,255,255,0.8);
            font-size: 0.9rem;
        }
        
        .chat-item:hover {
            background-color: rgba(255,255,255,0.1);
        }
        
        .chat-item.active {
            background-color: rgba(102, 126, 234, 0.3);
            border-color: #667eea;
            color: white;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stButton > button {
            border-radius: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render enhanced sidebar with navigation"""
        with st.sidebar:
            # Header
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">🌊 ARGO</h1>
                <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.9rem;">Welcome, {st.session_state['username']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation menu
            st.markdown("### 📍 Navigation")
            
            # Chat section
            if st.button("💬 Chat Assistant", key="nav_chat", use_container_width=True, 
                        type="primary" if st.session_state.current_page == "chats" else "secondary"):
                st.session_state.current_page = "chats"
                st.rerun()
            
            if st.button("📈 Analytics", key="nav_analytics", use_container_width=True,
                        type="primary" if st.session_state.current_page == "analytics" else "secondary"):
                st.session_state.current_page = "analytics"
                st.rerun()
                
            if st.button("🗺️ Map View", key="nav_map", use_container_width=True,
                        type="primary" if st.session_state.current_page == "map" else "secondary"):
                st.session_state.current_page = "map"
                st.rerun()
            
            if st.button("🗄️ Database", key="nav_database", use_container_width=True,
                        type="primary" if st.session_state.current_page == "database" else "secondary"):
                st.session_state.current_page = "database"
                st.rerun()
            
            if st.button("👥 Users", key="nav_users", use_container_width=True,
                        type="primary" if st.session_state.current_page == "users" else "secondary"):
                st.session_state.current_page = "users"
                st.rerun()
            
            if st.button("🔄 NetCDF Converter", key="nav_converter", use_container_width=True,
                        type="primary" if st.session_state.current_page == "converter" else "secondary"):
                st.session_state.current_page = "converter"
                st.rerun()
            
            # Chat management (only show on chat page)
            # if st.session_state.current_page == "chats":
            #     st.markdown("---")
            #     st.markdown("### 💬 Chats")
                
            #     if st.button("➕ New Chat", key="new_chat_btn", use_container_width=True):
            #         self.new_chat()
                
            #     # Chat list with ChatGPT style
            #     current_id = getattr(self, 'chat_id', None)
            #     st.markdown('<div style="max-height: 400px; overflow-y: auto;">', unsafe_allow_html=True)
                
            #     for cid, msgs in st.session_state["chats"].items():
            #         title = st.session_state.get("chat_titles", {}).get(cid, f"Untitled Chat")
            #         # Truncate title if too long
            #         display_title = title[:25] + "..." if len(title) > 25 else title
            #         is_selected = cid == current_id
                    
            #         # Create clickable chat item
            #         chat_class = "chat-item active" if is_selected else "chat-item"
            #         chat_html = f"""
            #         <div class="{chat_class}" onclick="selectChat('{cid}')" title="{title}">
            #             💬 {display_title}
            #         </div>
            #         """
                    
            #         if st.button(f"💬 {display_title}", key=f"chat_{cid}", 
            #                    use_container_width=True,
            #                    help=title):
            #             self.select_chat(cid)
                
            #     st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Logout
            if st.button("🚪 Logout", key="logout_btn", use_container_width=True, type="primary"):
                # Clear all session state
                st.session_state.clear()
                st.rerun()

    def select_chat(self, chat_id):
        """Select a specific chat"""
        st.query_params["chat_id"] = chat_id
        self.chat_id = chat_id
        self.messages = st.session_state["chats"][self.chat_id]
        st.rerun()

    def new_chat(self):
        """Create a new chat"""
        chat_id = str(uuid.uuid4())
        st.session_state["chats"][chat_id] = []
        st.session_state["chat_titles"] = st.session_state.get("chat_titles", {})
        st.session_state["chat_titles"][chat_id] = f"Untitled Chat #{st.session_state['chat_counter']}"
        st.session_state["chat_counter"] += 1
        st.query_params["chat_id"] = chat_id
        self.chat_id = chat_id
        self.messages = st.session_state["chats"][self.chat_id]
        st.rerun()

    def get_map_analytics(self, lat, lon):
        """Get analytics for map location with caching"""
        # Create a key for caching based on rounded coordinates
        key = f"{round(lat, 1)}_{round(lon, 1)}"
        
        if key not in st.session_state["map_analytics_cache"]:
            # Generate new analytics for this location
            n_sensors = np.random.randint(15, 30)
            st.session_state["map_analytics_cache"][key] = {
                'sensors': n_sensors,
                'avg_temp': np.random.uniform(20.0, 35.0),
                'avg_depth': np.random.randint(1500, 5000),
                'avg_salinity': np.random.uniform(33.0, 36.0),
                'temp_change': np.random.uniform(-0.5, 0.5),
                'sensor_change': np.random.randint(-2, 5)
            }
        
        return st.session_state["map_analytics_cache"][key]

    def render_analytics_page(self):
        """Render enhanced analytics dashboard"""
        st.title("📊  Analytics ")
        
        # Generate enhanced sensor data
        all_sensors = pd.DataFrame({
            'sensor_id': [f'IO-{i:03d}' for i in range(1, 9)] + 
                        [f'BB-{i:03d}' for i in range(1, 7)] +
                        [f'AS-{i:03d}' for i in range(1, 7)] +
                        [f'PO-{i:03d}' for i in range(1, 7)],
            'uptime': np.random.uniform(95.0, 99.9, 26),
            'location': ['Indian Ocean'] * 8 + ['Bay of Bengal'] * 6 + ['Arabian Sea'] * 6 + ['Pacific Ocean'] * 6,
            'latitude': np.concatenate([
                np.random.uniform(-20, 20, 8),  # Indian Ocean
                np.random.uniform(10, 25, 6),   # Bay of Bengal
                np.random.uniform(10, 25, 6),   # Arabian Sea
                np.random.uniform(-20, 20, 6)   # Pacific Ocean
            ]),
            'longitude': np.concatenate([
                np.random.uniform(60, 100, 8),   # Indian Ocean
                np.random.uniform(80, 95, 6),    # Bay of Bengal
                np.random.uniform(55, 75, 6),    # Arabian Sea
                np.random.uniform(120, 180, 6)   # Pacific Ocean
            ]),
            'data_points': np.random.randint(800, 1200, 26),
            'temperature': np.random.uniform(20.0, 35.0, 26),
            'salinity': np.random.uniform(33.0, 36.0, 26),
            'depth': np.random.randint(1500, 5000, 26),
            'status': np.random.choice(['Active', 'Warning', 'Active'], 26, p=[0.8, 0.1, 0.1])
        })
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌊 Total Sensors", "26", delta="+3 this month")
        
        with col2:
            avg_temp = all_sensors['temperature'].mean()
            st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C", delta=f"{avg_temp-26.5:+.1f}°C")
        
        with col3:
            total_points = all_sensors['data_points'].sum()
            st.metric("📊 Data Points", f"{total_points:,}", delta="+12% today")
        
        with col4:
            avg_uptime = all_sensors['uptime'].mean()
            st.metric("⚡ Avg Uptime", f"{avg_uptime:.1f}%", delta="+0.3%")
            
        st.markdown("### 📤 Export Options")
        col2, col3 = st.columns(2)
        
        with col2:
            if st.button("🗺️ Export Sensor Locations", use_container_width=True):
                content = self.create_dummy_file("sensor_locations.json", "json")
                st.markdown(self.download_file("sensor_locations.json", content, "application/json"), unsafe_allow_html=True)
                self.show_toast("🗺️ Location data export ready!")
        
        with col3:
            if st.button("📈 Export Report", use_container_width=True):
                content = self.create_dummy_file("monthly_report.pdf", "text")
                st.markdown(self.download_file("monthly_report.pdf", content, "application/pdf"), unsafe_allow_html=True)
                self.show_toast("📈 Monthly report generated!")
        
        st.markdown("---")
        
        # All sensors section
        st.markdown("### 🌊 All ARGO Sensors")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            location_filter = st.selectbox("Filter by Location", 
                                         ["All"] + list(all_sensors['location'].unique()))
        with col2:
            status_filter = st.selectbox("Filter by Status", 
                                       ["All"] + list(all_sensors['status'].unique()))
        
        # Apply filters
        filtered_sensors = all_sensors.copy()
        if location_filter != "All":
            filtered_sensors = filtered_sensors[filtered_sensors['location'] == location_filter]
        if status_filter != "All":
            filtered_sensors = filtered_sensors[filtered_sensors['status'] == status_filter]
        
        # Display sensors in a table format
        st.markdown(f"**Showing {len(filtered_sensors)} of {len(all_sensors)} sensors**")
        
        for idx, sensor in filtered_sensors.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            
            with col1:
                status_class = "status-active" if sensor['status'] == 'Active' else "status-inactive"
                st.markdown(f"<div class='sensor-card'><strong>{sensor['sensor_id']}</strong><br><span class='{status_class}'>● {sensor['status']}</span></div>", 
                           unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div class='sensor-card'><strong>📍 {sensor['location']}</strong><br><small>Lat: {sensor['latitude']:.3f}, Lon: {sensor['longitude']:.3f}</small></div>", 
                           unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div class='sensor-card'><strong>⚡ {sensor['uptime']:.1f}%</strong><br><small>Uptime</small></div>", 
                           unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"<div class='sensor-card'><strong>📊 {sensor['data_points']}</strong><br><small>Data points</small></div>", 
                           unsafe_allow_html=True)
            
            with col5:
                st.write("")
                if st.button("View Info", key=f"info_{sensor['sensor_id']}", help="View details"):
                    modal_content = f"""
                    <strong>Location:</strong> {sensor['location']}<br>
                    <strong>Coordinates:</strong> {sensor['latitude']:.3f}°, {sensor['longitude']:.3f}°<br>
                    <strong>Temperature:</strong> {sensor['temperature']:.1f}°C<br>
                    <strong>Salinity:</strong> {sensor['salinity']:.1f} psu<br>
                    <strong>Depth:</strong> {sensor['depth']} m<br>
                    <strong>Status:</strong> {sensor['status']}<br>
                    <strong>Uptime:</strong> {sensor['uptime']:.1f}%<br>
                    <strong>Data Points:</strong> {sensor['data_points']}
                    """
                    self.show_modal(f"{sensor['sensor_id']} Details", modal_content)
        
        # Export options
       
    def render_chat_page(self):
        """Render the chat interface"""
        st.title("💬 ARGO Assistant")
        st.markdown("Ask questions about ARGO oceanography data")

        # Display existing messages
        for message in st.session_state["messages"]:
            self.display_message(message)
        
        # Chat input
        query = st.chat_input("Ask a question")
     
        if query:
            # Set chat title if this is the first message
            if len(self.messages) == 0:
                st.session_state["chat_titles"][self.chat_id] = query[:30]
            
            # Add user message
            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)
            st.chat_message("user").write(query)
            
            # Simulate assistant response
            with httpx.Client(timeout=60.0) as client:
                response = client.post(f"{self.api_url}/query", json={"query": query}, timeout=120.0)
                if response.status_code == 200:
                    messages = response.json()["messages"]
                    st.session_state["messages"] = messages
                    for message in messages:
                        # st.chat_message(message["role"]).write(message["content"])
                        self.display_message(message)

    def render_map_page(self):
        """Render the enhanced map view page"""
        st.title("🗺️ ARGO Ocean Data Visualization")
        st.markdown("Real-time oceanographic measurements from ARGO float sensors across Indian and Pacific Oceans")
        st.markdown("")
        # Initialize session state for map
        if "map_centered" not in st.session_state:
            st.session_state.map_centered = False
        
        # Get user's current location (Coimbatore, Tamil Nadu)
        current_lat, current_lon = 11.0168, 76.9558
        
        # Create realistic ARGO sensor data around Indian/Pacific Ocean
        argo_sensors = pd.DataFrame({
            'lat': [
                # Indian Ocean sensors
                8.5, 12.3, 15.7, 6.2, 9.8, 14.1, 18.4, 22.3, 
                # Bay of Bengal
                16.2, 19.5, 13.8, 11.4, 17.9, 20.1,
                # Arabian Sea  
                10.5, 8.9, 12.7, 15.3, 18.6, 21.2,
                # Pacific Ocean (closer region)
                25.1, 28.4, 23.7, 26.9, 30.2, 24.8
            ],
            'lon': [
                # Indian Ocean sensors
                78.2, 82.5, 85.1, 79.8, 83.4, 88.2, 86.7, 89.5,
                # Bay of Bengal
                84.3, 87.9, 81.6, 79.2, 85.8, 88.4,
                # Arabian Sea
                75.3, 73.1, 77.8, 74.6, 76.9, 78.5,
                # Pacific Ocean
                120.3, 125.7, 118.9, 123.4, 128.1, 121.8
            ],
            'temperature': [
                26.8, 28.2, 27.5, 29.1, 26.3, 25.9, 24.7, 23.8,
                27.9, 28.5, 29.3, 30.1, 26.8, 25.4,
                31.2, 32.1, 30.8, 29.7, 28.9, 27.6,
                22.1, 21.5, 23.4, 20.9, 19.8, 22.7
            ],
            'salinity': [
                34.2, 34.5, 34.1, 34.8, 34.3, 33.9, 34.6, 34.4,
                34.1, 34.7, 34.9, 35.2, 34.0, 33.8,
                35.8, 36.1, 35.4, 35.0, 34.7, 34.3,
                33.5, 33.2, 33.8, 33.1, 32.9, 33.6
            ],
            'depth': [
                2500, 3200, 2800, 3500, 2900, 3100, 3800, 4200,
                2200, 2600, 2400, 1900, 2700, 3000,
                3400, 3600, 3300, 2800, 2500, 2100,
                4500, 4800, 4200, 4600, 5000, 4400
            ],
            'location': [
                'IO-001', 'IO-002', 'IO-003', 'IO-004', 'IO-005', 'IO-006', 'IO-007', 'IO-008',
                'BB-001', 'BB-002', 'BB-003', 'BB-004', 'BB-005', 'BB-006',
                'AS-001', 'AS-002', 'AS-003', 'AS-004', 'AS-005', 'AS-006',
                'PO-001', 'PO-002', 'PO-003', 'PO-004', 'PO-005', 'PO-006'
            ]
        })
        
        # Control panel with clear descriptions
        show_location = True
        col2, col3, col4 = st.columns(3)
        
        with col2:
            temp_filter = st.selectbox("🌡️ **Temperature Range**", 
                                     options=["All", "Cold (<25°C)", "Moderate (25-30°C)", "Warm (>30°C)"],
                                     help="Filter sensors by water temperature")
            
        with col3:
            depth_filter = st.selectbox("🏔️ **Depth Range**", 
                                      options=["All", "Shallow (<3000m)", "Deep (>3000m)"],
                                      help="Filter sensors by ocean depth")
            
        with col4:
            region_filter = st.selectbox("🗺️ **Ocean Region**", 
                                       options=["All Regions", "Indian Ocean", "Bay of Bengal", "Arabian Sea", "Pacific Ocean"],
                                       help="Focus on specific ocean regions")
        
        # Apply filters
        filtered_data = argo_sensors.copy()
        
        if temp_filter == "Cold (<25°C)":
            filtered_data = filtered_data[filtered_data['temperature'] < 25]
        elif temp_filter == "Moderate (25-30°C)":
            filtered_data = filtered_data[(filtered_data['temperature'] >= 25) & (filtered_data['temperature'] <= 30)]
        elif temp_filter == "Warm (>30°C)":
            filtered_data = filtered_data[filtered_data['temperature'] > 30]
            
        if depth_filter == "Shallow (<3000m)":
            filtered_data = filtered_data[filtered_data['depth'] < 3000]
        elif depth_filter == "Deep (>3000m)":
            filtered_data = filtered_data[filtered_data['depth'] >= 3000]
            
        if region_filter == "Indian Ocean":
            filtered_data = filtered_data[filtered_data['location'].str.startswith('IO')]
        elif region_filter == "Bay of Bengal":
            filtered_data = filtered_data[filtered_data['location'].str.startswith('BB')]
        elif region_filter == "Arabian Sea":
            filtered_data = filtered_data[filtered_data['location'].str.startswith('AS')]
        elif region_filter == "Pacific Ocean":
            filtered_data = filtered_data[filtered_data['location'].str.startswith('PO')]
        
        # Determine map center and zoom
        if st.session_state.map_centered:
            map_center_lat, map_center_lon = current_lat, current_lon
            map_zoom = 6
        else:
            map_center_lat, map_center_lon = 15.0, 82.0  # Center around Indian Ocean
            map_zoom = 4
        
        # Create the map
        fig = go.Figure()
        
        # Add ARGO sensors with enhanced styling
        if len(filtered_data) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=filtered_data['lat'],
                lon=filtered_data['lon'],
                mode='markers',
                marker=dict(
                    size=[temp * 0.8 for temp in filtered_data['temperature']],  # Size based on temperature
                    color=filtered_data['temperature'],
                    colorscale='RdYlBu_r',  # Red-Yellow-Blue reversed for temperature
                    sizemode='diameter',
                    sizeref=1,
                    sizemin=8,
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Temperature (°C)", font=dict(color="white", size=14)),
                        tickfont=dict(color="white"),
                        x=1.02
                    ), # White border around markers
                ),
                text=filtered_data['location'],
                hovertemplate="<b>🌊 ARGO Sensor: %{text}</b><br>" +
                             "<b>🌡️ Temperature:</b> %{marker.color:.1f}°C<br>" +
                             "<b>🧂 Salinity:</b> " + filtered_data['salinity'].astype(str) + " psu<br>" +
                             "<b>🏔️ Depth:</b> " + filtered_data['depth'].astype(str) + "m<br>" +
                             "<b>📍 Position:</b> %{lat:.3f}, %{lon:.3f}<br>" +
                             "<extra></extra>",
                name="ARGO Float Sensors"
            ))
        
        # Add current location with enhanced styling
        if show_location:
            # Outer circle (5m radius, 50% opacity)
            fig.add_trace(go.Scattermapbox(
                lat=[current_lat],
                lon=[current_lon],
                mode='markers',
                marker=dict(
                    size=20,
                    color='rgba(0, 100, 255, 0.5)',
                    symbol='circle'
                ),
                hovertemplate="<b>📍 Your Location</b><br>" +
                             "<b>🏙️ City:</b> Coimbatore, Tamil Nadu<br>" +
                             "<b>📍 Coordinates:</b> %{lat:.4f}, %{lon:.4f}<br>" +
                             "<extra></extra>",
                name="Location Area",
                showlegend=False
            ))
            
            # Inner circle (3m radius, solid blue)
            fig.add_trace(go.Scattermapbox(
                lat=[current_lat],
                lon=[current_lon],
                mode='markers',
                marker=dict(
                    size=12,
                    color='rgb(0, 100, 255)',
                    symbol='circle',
                ),
                hovertemplate="<b>📍 Your Current Position</b><br>" +
                             "<b>🏙️ Coimbatore, Tamil Nadu</b><br>" +
                             "<b>📍 Coordinates:</b> %{lat:.4f}, %{lon:.4f}<br>" +
                             "<extra></extra>",
                name="Your Location"
            ))
        
        # Add location centering button as a custom annotation (bottom right)
      
        
        # Update layout with enhanced styling
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=map_center_lat, lon=map_center_lon),
                zoom=map_zoom
            ),
            height=700,
            font=dict(color="white"),
            title=dict(
                text=f"Live ARGO Ocean Data - {len(filtered_data)} Active Sensors",
                font=dict(size=16, color="white"),
                x=0
            ),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=2,
                font=dict(color="black", size=12)
            ),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        # Display the map
        st.plotly_chart(fig, use_container_width=True)
        
        
        if st.button("🎯 Center Map to My Location", key="center_btn"):
                st.session_state.map_centered = True
                st.rerun()
      
        st.markdown("---")
        # Data summary with enhanced metrics
        st.markdown("### 📊 **Live Data Summary**")
        if len(filtered_data) > 0:
            st.success(f"✅ **{len(filtered_data)} ARGO sensors** are currently active and transmitting data in the selected region(s).")
        else:
            st.warning("⚠️ No sensors match the current filter criteria. Try adjusting the filters above.")
        st.markdown("")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_temp = filtered_data['temperature'].mean() if len(filtered_data) > 0 else 0
            st.metric("🌡️ **Average Temperature**", f"{avg_temp:.1f}°C", 
                     delta=f"+{(avg_temp - 26.5):.1f}°C vs baseline")
        
        with col2:
            active_sensors = len(filtered_data)
            st.metric("📡 **Active Sensors**", f"{active_sensors}", 
                     delta=f"{active_sensors - 20} vs last month")
        
        with col3:
            avg_depth = filtered_data['depth'].mean() if len(filtered_data) > 0 else 0
            st.metric("🏔️ **Average Depth**", f"{avg_depth:.0f}m", 
                     delta="Operational range")
        
        with col4:
            avg_salinity = filtered_data['salinity'].mean() if len(filtered_data) > 0 else 0
            st.metric("🧂 **Average Salinity**", f"{avg_salinity:.1f} psu", 
                     delta="Normal range")
        

    def render_database_page(self):
        """Render database management page"""
        st.title("📂 DB Files Management")
        
        # Initialize base database files if not exists
        if "base_db_files" not in st.session_state:
            st.session_state["base_db_files"] = pd.DataFrame({
                'filename': ['argo_sensors.sql', 'temperature_data.sql', 'salinity_readings.sql', 
                            'sensor_locations.sql', 'monthly_summaries.sql'],
                'size': ['2.3 MB', '15.7 MB', '8.9 MB', '1.1 MB', '4.2 MB'],
                'modified': ['2024-01-15 10:30', '2024-01-15 09:45', '2024-01-15 08:20', 
                            '2024-01-14 16:10', '2024-01-14 14:25'],
                'type': ['Table Schema', 'Sensor Data', 'Sensor Data', 'Configuration', 'Analytics']
            })
        
        # Combine base files with uploaded files
        all_files = st.session_state["base_db_files"].copy()
        for uploaded_file_info in st.session_state.get("uploaded_files", []):
            new_row = pd.DataFrame([uploaded_file_info])
            all_files = pd.concat([all_files, new_row], ignore_index=True)
        
        # File upload section
        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader("📤 Upload SQL File", type=['sql'], key="db_upload")
        with col2:
            st.write("")  
            st.write("")  
            st.write("")  
            if st.button("📤 Upload", disabled=uploaded_file is None):
                if uploaded_file:
                    # Check if it's a SQL file
                    if uploaded_file.name.lower().endswith('.sql'):
                        # Add to uploaded files list
                        file_info = {
                            'filename': uploaded_file.name,
                            'size': f"{len(uploaded_file.getvalue()) / 1024:.1f} KB",
                            'modified': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'type': 'User Upload'
                        }
                        if "uploaded_files" not in st.session_state:
                            st.session_state["uploaded_files"] = []
                        st.session_state["uploaded_files"].append(file_info)
                        self.show_toast(f"✅ SQL file '{uploaded_file.name}' uploaded successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Please upload only SQL files")
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])
        with col1:
            st.markdown("<span style='fontSize:16px'>**File Name**</span>",unsafe_allow_html=True)
        with col2:
            st.markdown("**Size**")
        with col3:
            st.markdown("**Date Added**")
        with col4:
            st.markdown("**Actions**")
        
        # Files table
        for idx, file_info in all_files.iterrows():
            col1, col2, col3, col4, col6, col7 = st.columns([2, 1, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**📄 {file_info['filename']}**<br><small>{file_info['type']}</small>", 
                           unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**{file_info['size']}**")
            
            with col3:
                st.markdown(f"<small>{file_info['modified']}</small>", unsafe_allow_html=True)
            
            with col4:
                if st.button("📥 Download", key=f"download_{idx}", help="Download"):
                    content = self.create_dummy_file(file_info['filename'], "sql")
                    st.markdown(self.download_file(file_info['filename'], content, "text/sql"), unsafe_allow_html=True)
                    self.show_toast(f"📥 {file_info['filename']} download ready!")
          
            with col6:
                if st.button("🏷️ Rename", key=f"rename_{idx}", help="Rename"):
                    st.session_state[f"renaming_{idx}"] = True
            
            with col7:
                if st.button("🗑️ Delete", key=f"delete_{idx}", help="Delete"):
                    # Remove from uploaded files if it's a user upload
                    if file_info['type'] == 'User Upload':
                        st.session_state["uploaded_files"] = [
                            f for f in st.session_state.get("uploaded_files", [])
                            if f['filename'] != file_info['filename']
                        ]
                    self.show_toast(f"🗑️ {file_info['filename']} deleted", "error")
                    st.rerun()
            
            # Show rename input if renaming
            if st.session_state.get(f"renaming_{idx}", False):
                new_name = st.text_input(f"New name for {file_info['filename']}", 
                                       value=file_info['filename'], key=f"rename_input_{idx}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.button("💾 Save", key=f"save_rename_{idx}"):
                        st.session_state[f"renaming_{idx}"] = False
                        self.show_toast(f"✏️ Renamed to {new_name}")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_rename_{idx}"):
                        st.session_state[f"renaming_{idx}"] = False
                        st.rerun()

    def render_users_page(self):
        """Render user management page"""
        st.title("👥 User Management")
        
        users_data = st.session_state["users_data"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = len(users_data)
            st.metric("👥 Total Users", total_users)
        
        with col2:
            active_users = len(users_data[users_data['status'] == 'active'])
            st.metric("🟢 Active Users", active_users)
        
        with col3:
            inactive_users = len(users_data[users_data['status'] == 'inactive'])
            st.metric("🔴 Inactive Users", inactive_users)
        
        with col4:
            admin_users = len(users_data[users_data['role'] == 'Administrator'])
            st.metric("👑 Administrators", admin_users)

        # Add new user section
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_email = st.text_input("**📧 Email**")
                    new_password = st.text_input("**🔒 Password**", type="password")
                with col2:
                    new_role = st.selectbox("**👤 Role**", ["User", "Administrator", "Superadmin"])
                    new_status = st.selectbox("**📊 Status**", ["active", "inactive"])
                
                if st.form_submit_button("➕ Add User"):
                    if new_email and new_password:
                        # Add new user to dataframe
                        new_user = pd.DataFrame([{
                            'email': new_email,
                            'password': new_password,
                            'status': new_status,
                            'role': new_role,
                            'last_login': 'Never'
                        }])
                        st.session_state["users_data"] = pd.concat([st.session_state["users_data"], new_user], ignore_index=True)
                        self.show_toast(f"✅ User {new_email} added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")
        
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 1])
        with col1:
            st.write("**Email Address**")
        with col2:
            st.write("**Password**")
        with col3:
            st.write("**Status**")
        with col4:
            st.write("**Role**")
        with col5:
            st.write("**Actions**")
        
        # Users table
        for idx, user in users_data.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 1])
            
            with col1:
                st.markdown(f"{user['email']}", 
                           unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"`{hashlib.md5(user['password'].encode('utf-8')).hexdigest()[:8]}...`", 
                           unsafe_allow_html=True)
            
            with col3:
                if user['status'] == 'active':
                    st.markdown('<span class="status-active">🟢 Active</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-inactive">🔴 Inactive</span>', unsafe_allow_html=True)
            
            with col4:
                # Role selection
                current_role_idx = ["User", "Administrator", "Superadmin"].index(user['role'])
                new_role = st.selectbox("", ["User", "Administrator", "Superadmin"], 
                                      index=current_role_idx, key=f"role_{idx}",label_visibility="collapsed")
                
                # Update role if changed
                if new_role != user['role']:
                    st.session_state["users_data"].loc[idx, 'role'] = new_role
                    self.show_toast(f"🔄 Role updated for {user['email']}")
            
            with col5:
                # Status toggle button
                if user['status'] == 'active':
                    if st.button("🔴 Deactivate", key=f"deactivate_{idx}"):
                        st.session_state["users_data"].loc[idx, 'status'] = 'inactive'
                        self.show_toast(f"🔴 User {user['email']} deactivated", "error")
                        st.rerun()
                else:
                    if st.button("🟢 Activate", key=f"activate_{idx}"):
                        st.session_state["users_data"].loc[idx, 'status'] = 'active'
                        self.show_toast(f"🟢 User {user['email']} activated")
                        st.rerun()
        
        st.markdown("---")
       
    def render_converter_page(self):
        """Render NetCDF to SQL converter page"""
        st.title("🔄 NetCDF to SQL Converter")
        st.markdown("Convert NetCDF oceanographic files to SQL database format")
        
        # File upload section
        st.markdown("### 📂 Select NetCDF File")
        uploaded_file = st.file_uploader("Choose a NetCDF file", type=['nc', 'netcdf'], key="netcdf_upload")
        
        if uploaded_file is not None:
            st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
            st.markdown(f"**File size:** {len(uploaded_file.getvalue()) / 1024:.2f} KB")
            
            # Conversion options
            st.markdown("---")
            st.markdown("### ⚙️ Conversion Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                table_name = st.text_input("📋 Table Name", value="argo_data")
                include_metadata = st.checkbox("📝 Include Metadata Tables", value=True)
                
            with col2:
                batch_size = st.number_input("📦 Batch Size", min_value=100, max_value=10000, value=1000)
                create_indices = st.checkbox("🔍 Create Database Indices", value=True)
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                col1, col2 = st.columns(2)
                with col1:
                    timestamp_format = st.selectbox("📅 Timestamp Format", 
                                                   ["ISO 8601", "Unix Timestamp", "Custom"])
                    null_handling = st.selectbox("❌ NULL Value Handling", 
                                                ["Skip", "Replace with 0", "Replace with NULL"])
                with col2:
                    data_types = st.multiselect("📊 Data Types to Include", 
                                              ["Temperature", "Salinity", "Pressure", "Depth", "Coordinates"],
                                              default=["Temperature", "Salinity", "Depth"])
                    compression = st.checkbox("🗜️ Compress SQL Output", value=False)
            
            # Convert button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🚀 Convert to SQL", key="convert_btn", use_container_width=True):
                    # Processing animation
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate conversion process
                    steps = [
                        ("🔍 Reading NetCDF file...", 0.2),
                        ("📊 Analyzing data structure...", 0.4),
                        ("🔄 Converting to SQL format...", 0.6),
                        ("📝 Generating SQL schema...", 0.8),
                        ("✅ Conversion complete!", 1.0)
                    ]
                    
                    for step_text, progress in steps:
                        status_text.text(step_text)
                        progress_bar.progress(progress)
                        time.sleep(1)
                    
                    status_text.empty()
                    progress_bar.empty()
                    st.success("🎉 Conversion completed successfully!")
                    
                    # Show conversion results
                    st.markdown("### 📋 Conversion Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Records Processed", "15,847")
                    with col2:
                        st.metric("📋 Tables Created", "3")
                    with col3:
                        st.metric("💾 Output Size", "2.3 MB")
                    
                    # Download and import options
                    st.markdown("---")
                    st.markdown("### 📤 Output Options")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📥 Download SQL File", key="download_converted_sql", use_container_width=True):
                            content = self.create_dummy_file(f"{table_name}_converted.sql", "sql")
                            st.markdown(self.download_file(f"{table_name}_converted.sql", content, "text/sql"), 
                                      unsafe_allow_html=True)
                            self.show_toast("📥 SQL file download ready!")
                    
                    with col2:
                        if st.button("📊 Import to Database", key="import_to_db", use_container_width=True):
                            # Add converted file to database files list
                            converted_file_info = {
                                'filename': f"{table_name}_converted.sql",
                                'size': "2.3 MB",
                                'modified': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'type': 'NetCDF Conversion'
                            }
                            if "uploaded_files" not in st.session_state:
                                st.session_state["uploaded_files"] = []
                            st.session_state["uploaded_files"].append(converted_file_info)
                            self.show_toast("📊 Data imported to database successfully!")
        
        else:
            # Show example/demo section
            st.markdown("---")
            st.markdown("### 💡 About NetCDF Conversion")
            
            st.info("""
            **NetCDF (Network Common Data Form)** is a widely used format for oceanographic data. 
            This converter helps you transform NetCDF files into SQL database format for easier analysis.
            
            **Supported Features:**
            - 🌡️ Temperature data
            - 🧂 Salinity measurements  
            - 🏔️ Depth/Pressure readings
            - 📍 Geographic coordinates
            - ⏰ Timestamp information
            - 📝 Metadata preservation
            """)
            
            # Sample data preview
            st.markdown("### 📊 Sample Output Preview")
            
            sample_sql = """
CREATE TABLE argo_data (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(20),
    timestamp TIMESTAMP,
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    temperature DECIMAL(5,2),
    salinity DECIMAL(5,2),
    depth INTEGER
);

INSERT INTO argo_data VALUES 
(1, 'ARGO_001', '2024-01-15 10:00:00', 15.2340, 82.4567, 26.8, 34.2, 2500),
(2, 'ARGO_001', '2024-01-15 10:05:00', 15.2341, 82.4568, 26.7, 34.3, 2510);
            """
            
            st.code(sample_sql, language='sql')

    def run(self):
        """Main application runner"""
        st.set_page_config(
            page_title="ARGO Ocean Analytics",
            page_icon="🌊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Setup custom CSS
        self.setup_custom_css()
        
        # Check authentication
        if not st.session_state["authenticated"]:
            self.login_page()
            return
        
        # Render sidebar
        self.render_sidebar()
        
        # Render main content based on current page
        if st.session_state.current_page == "chats":
            self.render_chat_page()
        elif st.session_state.current_page == "analytics":
            self.render_analytics_page()
        elif st.session_state.current_page == "map":
            self.render_map_page()
        elif st.session_state.current_page == "database":
            self.render_database_page()
        elif st.session_state.current_page == "users":
            self.render_users_page()
        elif st.session_state.current_page == "converter":
            self.render_converter_page()

# Run the application
if __name__ == "__main__":
    app = ArgoApp()
    app.run()