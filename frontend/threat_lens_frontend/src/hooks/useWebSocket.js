import { useEffect, useState, useRef, useCallback } from 'react';

export function useWebSocket() {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);

  const connect = useCallback(() => {
    const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    
    try {
      ws.current = new WebSocket(`${WS_URL}/ws`);
      
      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setConnected(true);
      };
      
      ws.current.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setConnected(false);
        
        // Reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('🔄 Reconnecting...');
          connect();
        }, 3000);
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages(prev => [data, ...prev].slice(0, 100));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return { messages, connected };
}
