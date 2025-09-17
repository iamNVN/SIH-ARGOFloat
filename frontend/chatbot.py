#Only 2 msgs are being shown at a time
#Move user message user icon to right side
#Add analytics page

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

class Chatbot:
    def __init__(self, api_url: str):
        self.api_url = api_url
        # Initialize chats dict and chat counter in session state
        if "chats" not in st.session_state:
            st.session_state["chats"] = {}
        if "chat_counter" not in st.session_state:
            st.session_state["chat_counter"] = 1
        # Get chat_id from URL or create new
        query_params = st.query_params
        chat_id = query_params["chat_id"] if query_params else None
        if not chat_id or chat_id not in st.session_state["chats"]:
            chat_id = str(uuid.uuid4())
            st.session_state["chats"][chat_id] = []
            st.session_state["chat_titles"] = st.session_state.get("chat_titles", {})
            st.session_state["chat_titles"][chat_id] = f"Untitled Chat #{st.session_state['chat_counter']}"
            st.session_state["chat_counter"] += 1
            st.query_params["chat_id"] = chat_id
        self.chat_id = chat_id
        self.messages = st.session_state["chats"][self.chat_id]

    def select_chat(self, chat_id):
        st.query_params["chat_id"] = chat_id
        st.session_state["selected_chat_id"] = chat_id
        st.rerun()

    def new_chat(self):
        chat_id = str(uuid.uuid4())
        st.session_state["chats"][chat_id] = []
        st.session_state["chat_titles"] = st.session_state.get("chat_titles", {})
        st.session_state["chat_titles"][chat_id] = f"Untitled Chat #{st.session_state['chat_counter']}"
        st.session_state["chat_counter"] += 1
        st.query_params["chat_id"] = chat_id
        st.session_state["selected_chat_id"] = chat_id
        st.rerun()

    def setup_custom_css(self):
        """Setup custom CSS for admin dashboard styling"""
        st.markdown("""
        <style>
        /* Main app styling */
        .main .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .sidebar-content {
            color: white;
        }
        
        /* Chat message styling */
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
        
        .stChatMessage.user {
            flex-direction: row-reverse;
        }
        
        /* Typing animation */
        .typing-indicator {
            display: flex;
            align-items: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 0.8rem;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes typing {
            0%, 80%, 100% {
                transform: scale(0);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #ffffff1A 0%, #ffffff0D 100%);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            border-radius: .8rem;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 255, 255, 0.05);
        }
        
        /* Status indicators */
        .status-card {
            background: white;
            padding: .5rem 1rem;
            border-radius: 0.8rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }
        
        /* Navigation styling */
        .nav-item {
            padding: 0.75rem 1rem;
            margin: 0.25rem 0;
            border-radius: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            color: white;
        }
        
        .nav-item:hover {
            background: rgba(255,255,255,0.1);
            transform: translateX(5px);
        }
        
        .nav-item.active {
            background: rgba(255,255,255,0.2);
            border-left: 3px solid white;
        }
        </style>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render sidebar using Streamlit native components with custom styling"""
        with st.sidebar:
            # Header
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <h1 style="color: white; margin: 0; font-size: 1.5rem;">🌊 ARGO</h1>
            </div>
            """, unsafe_allow_html=True)
            
            # Chats section
            st.markdown("### 📍 Chats")
            
            # New Chat button
            if st.button("➕ New Chat", key="newchatbtn", use_container_width=True):
                st.session_state.current_page = "chats"
                st.query_params['page'] = "chats"
                self.new_chat()
            
            # Chat list
            current_id = self.chat_id
            for cid, msgs in st.session_state["chats"].items():
                title = st.session_state.get("chat_titles", {}).get(cid, f"Untitled Chat")
                is_selected = cid == current_id
                
                if st.button(f"💬 {title}", key=f"chatbtn_{cid}", help=title, 
                           type="primary" if is_selected else "secondary", 
                           use_container_width=True):
                    st.session_state.current_page = "chats"
                    st.query_params['page'] = "chats"
                    self.select_chat(cid)
            
            st.markdown("---")
            
            # Navigation
            if st.button("📈 Analytics", key="analyticsbtn", use_container_width=True):
                st.session_state.current_page = "analytics"
                st.query_params['page'] = "analytics"
                st.rerun()
                
            if st.button("🗺️ Map View", key="mapbtn", use_container_width=True):
                st.session_state.current_page = "map"
                st.query_params['page'] = "map"
                st.rerun()
            
            st.markdown("---")
            
            # Logout
            if st.button(" Logout", key="logoutbtn", use_container_width=True, type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                
    def render_analytics_page(self):
        """Render the analytics dashboard page"""
        st.title("📊 ARGO Analytics Dashboard")
        
        # Generate sample analytics data
        import numpy as np
        from datetime import datetime, timedelta
        
        # Time series data for the last 30 days
        dates = [(datetime.now() - timedelta(days=x)) for x in range(30, 0, -1)]
        
        # Temperature trends
        temp_data = pd.DataFrame({
            'date': dates,
            'avg_temp': 26.5 + np.sin(np.linspace(0, 4*np.pi, 30)) * 2 + np.random.normal(0, 0.5, 30),
            'max_temp': 29.2 + np.sin(np.linspace(0, 4*np.pi, 30)) * 1.5 + np.random.normal(0, 0.3, 30),
            'min_temp': 23.8 + np.sin(np.linspace(0, 4*np.pi, 30)) * 1.8 + np.random.normal(0, 0.4, 30)
        })
        
        # Key metrics row
        st.markdown("")
        st.markdown("")
        st.markdown("### 🎯 **Key Performance Indicators**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                " **Total Active Sensors**", 
                "26", 
                delta="+3 this month",
                help="Currently operational ARGO float sensors"
            )
        
        with col2:
            current_temp = temp_data['avg_temp'].iloc[-1]
            prev_temp = temp_data['avg_temp'].iloc[-7]
            st.metric(
                " **Current Avg Temperature**", 
                f"{current_temp:.1f}°C",
                delta=f"{current_temp - prev_temp:+.1f}°C vs last week",
                help="Average ocean temperature across all sensors"
            )
        
        with col3:
            st.metric(
                " **Data Points Today**", 
                "1,247",
                delta=" +156 vs yesterday",
                help="Total measurements received today"
            )
        
        with col4:
            st.metric(
                " **System Uptime**", 
                "99.8%",
                delta=" +0.2% this month",
                help="Overall system availability"
            )
        
        # Charts section
        st.markdown("---")
        st.markdown("### 📈 **Temperature Trends Analysis**")
        
        # Temperature time series
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_temp = go.Figure()
            
            fig_temp.add_trace(go.Scatter(
                x=temp_data['date'],
                y=temp_data['avg_temp'],
                mode='lines+markers',
                name='Average Temperature',
                line=dict(color='#667eea', width=3),
                marker=dict(size=6)
            ))
            
            fig_temp.add_trace(go.Scatter(
                x=temp_data['date'],
                y=temp_data['max_temp'],
                mode='lines',
                name='Maximum Temperature',
                line=dict(color='#ff6b6b', width=2, dash='dot'),
            ))
            
            fig_temp.add_trace(go.Scatter(
                x=temp_data['date'],
                y=temp_data['min_temp'],
                mode='lines',
                name='Minimum Temperature',
                line=dict(color='#4ecdc4', width=2, dash='dot'),
            ))
            
            fig_temp.update_layout(
                title="30-Day Temperature Trend",
                xaxis_title="Date",
                yaxis_title="Temperature (°C)",
                height=400,
                font=dict(color="white"),
                legend=dict(
                    bgcolor="rgba(255,255,255,0.05)",
                    bordercolor="rgba(255,255,255,0.2)",
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col2:
            # Temperature distribution
            fig_dist = go.Figure(data=go.Histogram(
                x=temp_data['avg_temp'],
                nbinsx=10,
                marker_color='#667eea',
                opacity=0.7
            ))
            
            fig_dist.update_layout(
                title="Temperature Distribution",
                xaxis_title="Temperature (°C)",
                yaxis_title="Frequency",
                height=400,
                font=dict(color="white")
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
        
        # Regional analysis
        st.markdown("---")
        
        st.markdown("### 🗺️ **Regional Data Analysis**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Regional sensor distribution
            regions = ['Indian Ocean', 'Bay of Bengal', 'Arabian Sea', 'Pacific Ocean']
            sensor_counts = [8, 6, 6, 6]
            
            fig_pie = go.Figure(data=go.Pie(
                labels=regions,
                values=sensor_counts,
                marker_colors=['#667eea', '#764ba2', '#ff6b6b', '#4ecdc4']
            ))
            
            fig_pie.update_layout(
                title="Sensor Distribution by Region",
                height=400,
                font=dict(color="white")
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Average temperature by region
            region_temps = pd.DataFrame({
                'Region': regions,
                'Avg_Temperature': [27.2, 28.1, 30.5, 22.8],
                'Sensor_Count': sensor_counts
            })
            
            fig_bar = go.Figure(data=go.Bar(
                x=region_temps['Region'],
                y=region_temps['Avg_Temperature'],
                marker_color=['#667eea', '#764ba2', '#ff6b6b', '#4ecdc4'],
                text=region_temps['Avg_Temperature'].round(1),
                textposition='auto'
                
            ))
            
            fig_bar.update_layout(
                title="Average Temperature by Region",
                xaxis_title="Ocean Region",
                
                yaxis_title="Temperature (°C)",
                height=400,
                font=dict(color="white")
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Data quality metrics
        st.markdown("---")
        
        st.markdown("### 🔍 **Data Quality & System Health**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Data completeness gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = 97.8,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Data Completeness (%)"},
                delta = {'reference': 95},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 85], 'color': "red"},
                        {'range': [85, 90], 'color': "yellow"},
                        {'range': [90, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 94
                    }
                }
            ))
            
            fig_gauge.update_layout(height=300, font=dict(color="white"))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Recent alerts
            st.markdown("#### 🚨 Recent Alerts")
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                <div style="color: #28a745;">✅ All sensors operational</div>
                <small style="color: #666;">2 hours ago</small>
            </div>
            <div style="background: #fff3cd; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                <div style="color: #856404;">⚠️ High temperature detected in AS-001</div>
                <small style="color: #666;">6 hours ago</small>
            </div>
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
                <div style="color: #28a745;">✅ Data transmission restored PO-003</div>
                <small style="color: #666;">1 day ago</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Top performing sensors
            st.markdown("#### 🏆 Top Sensors")
            top_sensors = pd.DataFrame({
                'Sensor': ['BB-002', 'IO-005', 'AS-001', 'PO-001'],
                'Uptime': ['99.9%', '99.7%', '99.5%', '99.2%'],
                'Data_Points': [1024, 987, 945, 912]
            })
            
            for idx, row in top_sensors.iterrows():
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 0.5rem; margin: 0.3rem 0; border-left: 4px solid #667eea;">
                    <div style="font-weight: bold; color: #333;">{row['Sensor']}</div>
                    <div style="color: #666; font-size: 0.9rem;">Uptime: {row['Uptime']} | Points: {row['Data_Points']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Export options
        st.markdown("---")
        
        st.markdown("### 📤 **Data Export Options**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Export Temperature Data", use_container_width=True):
                st.success("📊 Temperature data exported to CSV")
        
        with col2:
            if st.button("🗺️ Export Sensor Locations", use_container_width=True):
                st.success("🗺️ Location data exported to JSON")
        
        with col3:
            if st.button("📈 Generate Report", use_container_width=True):
                st.success("📈 Monthly report generated")
        
        with col4:
            if st.button("⚙️ System Diagnostics", use_container_width=True):
                st.success("⚙️ Diagnostic report ready")
        
     

    def render_chat_page(self):
        """Render the chat interface"""
        st.title("💬 ARGO Assistant")
        st.markdown("Ask questions and get answers to the ARGO oceanography data")

        # Display existing messages for current chat
        for message in st.session_state["chats"][self.chat_id]:
            if message["role"] == "user" and isinstance(message["content"], str):
                st.chat_message("user").write(message["content"])
            elif message["role"] == "assistant" and isinstance(message["content"], str):
                st.chat_message("assistant").write(message["content"])
        
        # Chat input
        query = st.chat_input("Ask a question")
        if query:
            # Set chat title if this is the first message
            if len(st.session_state["chats"][self.chat_id]) == 0:
                st.session_state["chat_titles"][self.chat_id] = query[:30] or st.session_state["chat_titles"][self.chat_id]
            user_message = {"role": "user", "content": query}
            st.session_state["chats"][self.chat_id].append(user_message)
            
            # Display user message immediately
            st.chat_message("user").write(query)
            
            # Show typing animation
            typing_placeholder = st.empty()
            with typing_placeholder.container():
                st.markdown("""
                <div style="display: flex; align-items: center; padding: 1rem; background-color: rgba(38, 39, 48, 0.5); border-radius: 0.8rem; margin: 1rem 0; border-left: 4px solid #667eea;">
                    <div style="margin-right: 10px; color: white;">ARGO Assistant is thinking...</div>
                    <div style="display: flex; gap: 4px;">
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: #667eea; animation: typing 1.4s infinite ease-in-out; animation-delay: -0.32s;"></div>
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: #667eea; animation: typing 1.4s infinite ease-in-out; animation-delay: -0.16s;"></div>
                        <div style="width: 8px; height: 8px; border-radius: 50%; background: #667eea; animation: typing 1.4s infinite ease-in-out;"></div>
                    </div>
                </div>
                <style>
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
                    40% { transform: scale(1); opacity: 1; }
                }
                </style>
                """, unsafe_allow_html=True)
            
            # Get response from API synchronously
            try:
                import httpx
                import time
                
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(f"{self.api_url}/query", json={"query": query})
                    
                    typing_placeholder.empty()  # Remove typing animation
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        # Only append the new assistant message, do not overwrite the chat
                        assistant_messages = [msg for msg in response_data.get("messages", []) if msg["role"] == "assistant"]
                        if assistant_messages and isinstance(assistant_messages[-1]["content"], str):
                            st.session_state["chats"][self.chat_id].append(assistant_messages[-1])
                            st.chat_message("assistant").write(assistant_messages[-1]["content"])
                            st.rerun()  # Refresh to show the new message
                    else:
                        error_msg = f"⚠️ Sorry, I encountered an error (Status: {response.status_code}). Please try again."
                        st.session_state["chats"][self.chat_id].append({"role": "assistant", "content": error_msg})
                        st.chat_message("assistant").write(error_msg)
                        st.rerun()
            
            except Exception as e:
                typing_placeholder.empty()  # Remove typing animation on error
                error_msg = f"⚠️ Connection error: {str(e)}. Please check if the server is running."
                st.session_state["chats"][self.chat_id].append({"role": "assistant", "content": error_msg})
                st.chat_message("assistant").write(error_msg)
                st.rerun()

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
        
        # Data insights
        

    async def get_tools(self) -> Dict[str, Any]:
        """Get available tools from API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/tools")
                return response.json()
        except:
            return {"tools": []}

    async def render(self):
        """Main render method"""
        # Setup custom CSS
        self.setup_custom_css()
        
        # Initialize session state
        if "current_page" not in st.session_state:
            st.session_state.current_page = "chats"
        
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        
        # Render sidebar
        self.render_sidebar()
        
        # Render main content based on selected page
        if st.session_state.current_page == "chats":
            self.render_chat_page()
        elif st.session_state.current_page == "map":
            self.render_map_page()
        
        elif st.session_state.current_page == "analytics":
            self.render_analytics_page()