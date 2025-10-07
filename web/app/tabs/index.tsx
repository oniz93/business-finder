
import React from 'react';
import { ScrollView, Text, TextInput, TouchableOpacity, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

const HomeScreen = () => {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        {/* Jumbotron */}
        <LinearGradient
          colors={['#1a202c', '#2d3748']}
          style={styles.jumbotron}
        >
          <Text style={styles.jumbotronTitle}>Find Your Next Big Idea</Text>
          <Text style={styles.jumbotronSubtitle}>
            AI-powered insights to uncover untapped business opportunities from Reddit.
          </Text>
          <TouchableOpacity style={styles.jumbotronButton}>
            <Text style={styles.jumbotronButtonText}>Join the Waitlist</Text>
          </TouchableOpacity>
        </LinearGradient>

        {/* Features Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Why Business Finder?</Text>
          <View style={styles.featuresGrid}>
            <View style={styles.featureCard}>
              <Ionicons name="search" size={32} color="#2563eb" />
              <Text style={styles.featureCardTitle}>Discover Opportunities</Text>
              <Text style={styles.featureCardText}>
                We analyze millions of conversations to find problems people are desperate to solve.
              </Text>
            </View>
            <View style={styles.featureCard}>
              <Ionicons name="document-text" size={32} color="#2563eb" />
              <Text style={styles.featureCardTitle}>Full Business Plans</Text>
              <Text style={styles.featureCardText}>
                Get comprehensive, AI-generated business plans for the most promising ideas.
              </Text>
            </View>
            <View style={styles.featureCard}>
              <Ionicons name="analytics" size={32} color="#2563eb" />
              <Text style={styles.featureCardTitle}>Market Analysis</Text>
              <Text style={styles.featureCardText}>
                Understand the market landscape with in-depth analysis and competitor insights.
              </Text>
            </View>
            <View style={styles.featureCard}>
              <Ionicons name="people" size={32} color="#2563eb" />
              <Text style={styles.featureCardTitle}>Team Collaboration</Text>
              <Text style={styles.featureCardText}>
                Work with your team to refine and build upon your next big venture.
              </Text>
            </View>
          </View>
        </View>

        {/* Testimonials Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What Our Users Say</Text>
          <View style={styles.testimonialCard}>
            <Text style={styles.testimonialText}>
              "Business Finder helped me discover a niche market I never would have found on my own. The business plan was a huge head start!"
            </Text>
            <Text style={styles.testimonialAuthor}>- Jane Doe, Founder of CoolNewStartup</Text>
          </View>
          <View style={styles.testimonialCard}>
            <Text style={styles.testimonialText}>
              "The quality of the insights is incredible. It's like having a team of researchers working for you 24/7."
            </Text>
            <Text style={styles.testimonialAuthor}>- John Smith, Serial Entrepreneur</Text>
          </View>
        </View>

        {/* Waitlist Section */}
        <View style={styles.waitlistSection}>
          <Text style={styles.waitlistTitle}>Get Early Access</Text>
          <Text style={styles.waitlistSubtitle}>
            Join the waitlist for our premium features and be the first to know when we launch.
          </Text>
          <View style={styles.waitlistForm}>
            <TextInput
              style={styles.input}
              placeholder="Enter your email"
              placeholderTextColor="#999"
            />
            <TouchableOpacity style={styles.button}>
              <Text style={styles.buttonText}>Join Waitlist</Text>
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
    backgroundColor: '#f0f2f5',
  },
  container: {
    paddingBottom: 48,
  },
  jumbotron: {
    padding: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  jumbotronTitle: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 16,
  },
  jumbotronSubtitle: {
    fontSize: 18,
    color: '#cbd5e0',
    textAlign: 'center',
    maxWidth: 600,
    marginBottom: 32,
  },
  jumbotronButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  jumbotronButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  section: {
    padding: 24,
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a202c',
    marginBottom: 24,
    textAlign: 'center',
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    width: '48%',
    marginBottom: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  featureCardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2d3748',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  featureCardText: {
    fontSize: 14,
    color: '#4a5568',
    textAlign: 'center',
  },
  testimonialCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  testimonialText: {
    fontSize: 16,
    color: '#4a5568',
    fontStyle: 'italic',
    marginBottom: 16,
  },
  testimonialAuthor: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2d3748',
    textAlign: 'right',
  },
  waitlistSection: {
    backgroundColor: '#ffffff',
    padding: 32,
    alignItems: 'center',
  },
  waitlistTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a202c',
    marginBottom: 16,
  },
  waitlistSubtitle: {
    fontSize: 16,
    color: '#4a5568',
    textAlign: 'center',
    maxWidth: 600,
    marginBottom: 24,
  },
  waitlistForm: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    maxWidth: 500,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#ffffff',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 8,
    fontSize: 16,
    color: '#2d3748',
    marginRight: 8,
  },
  button: {
    backgroundColor: '#2563eb',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default HomeScreen;
