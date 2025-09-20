import React, {
  createContext,
  useContext,
  useState,
  ReactNode,
  useEffect,
} from "react";

export type Message = {
  id: number;
  type: "question" | "answer" | "loading";
  text: string | React.ReactNode;
  isStreaming?: boolean;
  pdfUrl?: string | null;
  isPdfVisible?: boolean;
  pageNum?: number;
};

type ChatContextType = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) throw new Error("useChat must be used within a ChatProvider");
  return context;
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem("chatMessages");
    return saved ? JSON.parse(saved) : [];
  });

  // messages가 바뀔 때마다 localStorage에 저장
  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
