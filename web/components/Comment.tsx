import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface CommentProps {
  author: string;
  content: string;
  onReply: () => void;
}

const Comment: React.FC<CommentProps> = ({ author, content, onReply }) => {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.author}>{author}</Text>
      </View>
      <Text style={styles.content}>{content}</Text>
      <TouchableOpacity onPress={onReply} style={styles.replyButton}>
        <Text style={styles.replyButtonText}>Reply</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  author: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2d3748',
  },
  content: {
    fontSize: 16,
    color: '#4a5568',
    lineHeight: 24,
  },
  replyButton: {
    marginTop: 12,
    alignSelf: 'flex-start',
  },
  replyButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2563eb',
  },
});

export default Comment;