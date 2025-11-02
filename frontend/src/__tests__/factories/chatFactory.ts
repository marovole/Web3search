import { faker } from '@faker-js/faker';

export interface Message {
  id: string;
  conversationId: string;
  message: string;
  sender: 'user' | 'ai';
  timestamp: string;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  model: string;
  tokensUsed: number;
  processingTime: number;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messageCount: number;
}

export const createChatFactory = () => ({
  buildMessage: (overrides: Partial<Message> = {}): Message => ({
    id: `msg-${faker.string.uuid()}`,
    conversationId: `conv-${faker.string.uuid()}`,
    message: faker.lorem.paragraph(),
    sender: faker.helpers.arrayElement(['user', 'ai']),
    timestamp: faker.date.recent().toISOString(),
    metadata: {
      model: 'gpt-4',
      tokensUsed: faker.number.int({ min: 50, max: 500 }),
      processingTime: faker.number.float({ min: 0.5, max: 3.0, precision: 0.1 }),
    },
    ...overrides,
  }),

  buildMessages: (count: number, overrides: Partial<Message> = {}): Message[] =>
    Array.from({ length: count }, () => this.buildMessage(overrides)),

  buildConversation: (overrides: Partial<Conversation> = {}): Conversation => ({
    id: `conv-${faker.string.uuid()}`,
    title: faker.lorem.sentence(),
    lastMessage: faker.lorem.sentence(),
    timestamp: faker.date.recent().toISOString(),
    messageCount: faker.number.int({ min: 1, max: 50 }),
    ...overrides,
  }),

  buildConversations: (count: number, overrides: Partial<Conversation> = {}): Conversation[] =>
    Array.from({ length: count }, () => this.buildConversation(overrides)),

  // Predefined test data
  testConversation: (): Conversation => this.buildConversation({
    id: 'conv-test-1',
    title: 'Test Conversation',
    lastMessage: 'Hello, how can I help you?',
    messageCount: 5,
  }),

  testMessage: (conversationId = 'conv-test-1'): Message => this.buildMessage({
    id: 'msg-test-1',
    conversationId,
    message: 'Hello, how can I help you?',
    sender: 'ai',
  }),

  userMessage: (conversationId = 'conv-test-1', message = 'I need help'): Message => 
    this.buildMessage({
      conversationId,
      message,
      sender: 'user',
    }),

  aiMessage: (conversationId = 'conv-test-1', message = 'I can help you with that'): Message => 
    this.buildMessage({
      conversationId,
      message,
      sender: 'ai',
    }),

  // Create a conversation with alternating messages
  createConversationHistory: (userMessageCount: number, conversationId = `conv-${faker.string.uuid()}`): Message[] => {
    const messages: Message[] = [];
    
    // Start with AI greeting
    messages.push(this.buildMessage({
      id: `msg-${faker.string.uuid()}`,
      conversationId,
      message: 'Hello! How can I help you today?',
      sender: 'ai',
      timestamp: faker.date.past().toISOString(),
    }));

    // Add alternating user and AI messages
    for (let i = 0; i < userMessageCount; i++) {
      messages.push(this.userMessage(conversationId, faker.lorem.sentence()));
      messages.push(this.aiMessage(conversationId, faker.lorem.paragraph()));
    }

    return messages;
  },
});

export const chatFactory = createChatFactory();
