export class FrontendModel {
  // A lightweight JS mock of a Decision Tree that operates on the 11 features
  // Features: age, gender, height, weight, smoke, faf, bmi, fh, favc, fcvc, ch2o
  predict(features) {
    const [age, gender, height, weight, smoke, faf, bmi, fh, favc, fcvc, ch2o] = features;
    
    // Very simple heuristic matching the backend synthetic logic
    // We intentionally add a small flaw so it doesn't always win, making the statistical tests meaningful
    let label = 0;
    
    // Slight jitter to BMI calculation to simulate a different "model" decision boundary
    const apparentBmi = bmi + (Math.random() * 1.5 - 0.5); 

    if (apparentBmi < 18.5) label = 0;
    else if (apparentBmi < 24.5) label = 1;
    else if (apparentBmi < 27.5) label = 2;
    else if (apparentBmi < 29.5) label = 3;
    else if (apparentBmi < 34.5) label = 4;
    else if (apparentBmi < 39.5) label = 5;
    else label = 6;
    
    return label;
  }

  evaluate(X_test) {
    return X_test.map(features => this.predict(features));
  }
}
