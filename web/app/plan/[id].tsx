import { Stack, useLocalSearchParams } from 'expo-router';
import React from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import Comment from '../../components/Comment';

const BusinessPlanScreen = () => {
  const { id } = useLocalSearchParams();

  // Mock data for business plan
  const businessPlan = {
    title: `Business Plan ${id}`,
    description: 'This is a detailed business plan for the idea found on Reddit. This is a mock description. The real description will be much longer and more detailed.',
    sections: [
      { title: 'Executive Summary', content: 'This is the executive summary.' },
      { title: 'Market Analysis', content: 'This is the market analysis.' },
      { title: 'Marketing and Sales Strategy', content: 'This is the marketing and sales strategy.' },
      { title: 'Financial Projections', content: 'This is the financial projections.' },
    ],
  };

  const comments = [
    { id: 1, author: 'User1', content: 'This is a great idea!' },
    { id: 2, author: 'User2', content: 'I would suggest to focus more on the marketing side.' },
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient colors={['#ffffff', '#f0f2f5']} style={styles.gradient} />
      <Stack.Screen options={{ title: businessPlan.title }} />
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>{businessPlan.title}</Text>
          <Text style={styles.description}>{businessPlan.description}</Text>
        </View>

        {businessPlan.sections.map((section, index) => (
          <View key={index} style={styles.section}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            <Text style={styles.sectionContent}>{section.content}</Text>
          </View>
        ))}

        <View style={styles.commentsSection}>
          <Text style={styles.commentsTitle}>Comments</Text>
          {comments.map(comment => (
            <Comment
              key={comment.id}
              author={comment.author}
              content={comment.content}
              onReply={() => {}}
            />
          ))}

          <View style={styles.addCommentContainer}>
            <TextInput
              style={styles.input}
              placeholder="Add a comment"
              placeholderTextColor="#999"
            />
            <TouchableOpacity style={styles.button}>
              <Text style={styles.buttonText}>Post Comment</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    height: '100%',
  },
  container: {
    padding: 24,
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a202c',
    marginBottom: 8,
  },
  description: {
    fontSize: 18,
    color: '#4a5568',
  },
  section: {
    marginBottom: 24,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  sectionTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 16,
  },
  sectionContent: {
    fontSize: 16,
    color: '#4a5568',
    lineHeight: 24,
  },
  commentsSection: {
    marginTop: 32,
  },
  commentsTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2d3748',
    marginBottom: 16,
  },
  addCommentContainer: {
    marginTop: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    fontSize: 16,
    color: '#2d3748',
    marginBottom: 8,
  },
  button: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default BusinessPlanScreen;