import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, TouchableOpacity, SafeAreaView, StyleSheet } from 'react-native';
import { getRandomPlan } from '../services/api';
import { BusinessPlan } from '../types/business_plan';
import BusinessPlanCard from '../components/BusinessPlanCard';
import { LinearGradient } from 'expo-linear-gradient';

const FeedScreen = () => {
  const [plan, setPlan] = useState<BusinessPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRandomPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const randomPlan = await getRandomPlan();
      if (randomPlan) {
        setPlan(randomPlan);
      } else {
        setError('Failed to fetch business plan. Please try again.');
      }
    } catch (error) {
      setError('Failed to fetch business plan. Please try again.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRandomPlan();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#1e2a3a', '#12161f', '#0d1117']}
        style={styles.gradient}
      />
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.nextButton} onPress={loadRandomPlan}>
          <Text style={styles.nextButtonText}>Next Idea</Text>
        </TouchableOpacity>
      </View>
      {loading && (
        <View style={styles.centeredContainer}>
          <ActivityIndicator size="large" color="#ffffff" />
        </View>
      )}
      {error && (
        <View style={styles.centeredContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadRandomPlan}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}
      {plan && !loading && !error && (
        <BusinessPlanCard plan={plan} />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    height: '100%',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    padding: 10,
    alignItems: 'center',
  },
  nextButton: {
    backgroundColor: '#58a6ff',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  nextButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#ffffff',
    fontSize: 16,
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#ffffff',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 5,
  },
  retryButtonText: {
    color: '#0d1117',
    fontSize: 16,
  },
});

export default FeedScreen;

