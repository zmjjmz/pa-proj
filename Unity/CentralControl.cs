using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class CentralControl : MonoBehaviour {
  public class CPG{
    // All angular values are in radians
    private int n;
    private float[] a, theta, ampl, ampl_dot, signal;
    // Evolved values for the limb setpoint function
    private float[] gsl, gsh, gb1, gb2;
    // 0 for body, 1 for limb
    private int[] osc_class;
    private float[,] w, phi;
     
    // Parameters defined by table S1 (body, limb)
    private float[] cv0, cv1, cR0, cR1;
    // ( (dbody_low, dbody_high), (dlimb_low, dlimb_high) )
    private int[,] d_params;

    public CPG(int n, float[] a, float[] theta, float[] ampl, float[] ampl_dot, 
               int[] osc_class, float[,] w, float[,] phi, float[] gsl, 
               float[] gsh, float[] gb1, float[] gb2){
      cv0 = new float[] {0.3f, 0.0f};
      cv1 = new float[] {0.2f, 0.2f};
      cR0 = new float[] {0.196f, 0.131f};
      cR1 = new float[] {0.065f, 0.131f};
      d_params = new int[,]{ {1,5}, {1,3} };
      signal = new float[n];
      this.n = n;
      this.a = a;
      this.theta = theta;
      this.ampl = ampl;
      this.ampl_dot = ampl_dot;
      this.osc_class = osc_class;
      this.w = w;
      this.phi = phi;
      this.gsl = gsl;
      this.gsh = gsh;
      this.gb1 = gb1;
      this.gb2 = gb2;
    }
    
    // Calculate drives 
    private void drive(int d, ref float[] R, ref float[] v){
      for(int i = 0; i < n; i++){
        int is_limb_osc = osc_class[i];
        if(d >= d_params[is_limb_osc, 0] && d <= d_params[is_limb_osc, 1]){
          R[i] = cR1[is_limb_osc] * d + cR0[is_limb_osc];
          v[i] = cv1[is_limb_osc] * d + cv0[is_limb_osc];
        }
        else{
          R[i] = v[i] = 0;
        }
      }
    }
    
    // Steps the phase of each oscillator (theta) 
    private float[] step_theta(float[] v){
      float[] theta_dot = new float[n];
      float[] new_theta = new float[n];
      for(int i = 0; i < n; i++){
        theta_dot[i] = 2 * Mathf.PI * v[i];
        for(int j = 0; j < n; j++){
          theta_dot[i] += ampl[j] * w[i,j] * Mathf.Sin(theta[j] - theta[i] - phi[i,j]);
        }
        new_theta[i] = theta_dot[i] + theta[i];
      }
      return new_theta;
    }
    
    // Steps the 2nd order change in amplitude of each oscillator with the 
    // 1st order as a parameter, then steps the first order with that value
    private float[] step_ampl_dot(float[] R){
      float[] ampl_dot_dot = new float[n];
      float[] new_ampl_dot = new float[n];
      for(int i = 0; i < n; i++){
        ampl_dot_dot[i] = a[i] * (a[i]/4.0f * (R[i] - ampl[i] - ampl_dot[i]));
        new_ampl_dot[i] = ampl_dot[i] + ampl_dot_dot[i];
      }
      return new_ampl_dot;
    }
 
    // Set the signal for each oscillator (x)
    private void set_signals(){
      for(int i = 0; i < n; i++){
        signal[i] = ampl[i] * (1+Mathf.Cos(theta[i]));
      }
    }

    // Step the simulation, will be called by FixedUpdate()
    public void step(int d){
      float[] R = new float[n];
      float[] v = new float[n];
      drive(d, ref R, ref v);
        
      float[] new_theta = step_theta(v);
      float[] new_ampl_dot = step_ampl_dot(R);
      float[] new_ampl = new float[n];
      for(int i = 0; i < n; i++){
        new_ampl[i] = ampl[i] + new_ampl_dot[i];
      }

      set_signals();
        
      theta = new_theta;
      ampl_dot = new_ampl_dot;
      ampl = new_ampl;
    }
      
    // given the indices for a left and right pair of body oscillators and
    // the scalar alpha for them, return the setpoint (desired angle)
    // in radians
    public float get_body_setpoint(float alpha, int l_index, int r_index){
      return alpha*(signal[l_index] - signal[r_index]);
    }

    public float get_limb_setpoint(int i){
      return (theta[i] >= gb1[i] && theta[i] <= gb2[i]) ? gsh[i] * theta[i] : 
        gsl[i] * theta[i];
    }
  }

  // Joints and Oscillators can be indexed by their number on the 
  // salamander robot diagram minus 1
  public HingeJoint[] joints = new HingeJoint[10];

  // 16 body oscillators (12 of which map to 6 joints) and 4 limb 
  // oscillators, each of which maps to a limb
  public CPG salamander;

  // used for the placeholder drivers
  public System.Random rand = new System.Random();

  // Initialization of variables
  void Start () {
    int n = 20;
    int gen = 0;
    // Initialize the whole CPG structure
    float[] a, theta, ampl, ampl_dot, gsl, gsh, gb1, gb2;
    int[] osc_class;
    float[,] w, phi;
    getParams(n, out a, out theta, out ampl, out ampl_dot, out osc_class, 
              out w, out phi, out gsl, out gsh, out gb1, out gb2);
    salamander = new CPG(n, a, theta, ampl, ampl_dot, osc_class, w, phi, gsl, 
                         gsh, gb1, gb2);
    
    // Some segments have only one joint
    joints[0] = GameObject.Find("2").GetComponent<HingeJoint>();
    joints[1] = GameObject.Find("3").GetComponent<HingeJoint>();
    joints[3] = GameObject.Find("5").GetComponent<HingeJoint>();
    joints[4] = GameObject.Find("6").GetComponent<HingeJoint>();
    joints[5] = GameObject.Find("7").GetComponent<HingeJoint>();

    // Others have more than one joint, and these must be differentiated
    HingeJoint[] feet = GameObject.Find("1/Center").GetComponents<HingeJoint>();
    foreach(HingeJoint foot in feet){
      if(foot.connectedBody == 
         GameObject.Find("1/LeftFoot").GetComponent<Rigidbody>()){
        joints[6] = foot;
      }
      else{ 
        joints[7] = foot;
      }
    }
    feet = GameObject.Find("4/Center").GetComponents<HingeJoint>();
    foreach(HingeJoint foot in feet){
      if(foot.connectedBody == 
         GameObject.Find("4/LeftFoot").GetComponent<Rigidbody>()){
        joints[8] = foot;
      }
      else if(foot.connectedBody == 
              GameObject.Find("4/RightFoot").GetComponent<Rigidbody>()){
        joints[9] = foot;
      }
      // Also have to check for segment in front of this segment 
      else{
        joints[2] = foot;
      }
    }
  }

  // This function is called every .2 seconds of simulation, and is where motor 
  // changes will happen
  void FixedUpdate(){
    // We aren't actually using time yet . . .
    float time = Time.fixedTime;
    float stepTime = Time.deltaTime;
    float desiredAngle;
    float alpha = 0.5f;
    // Body joints
    for(int i = 0; i < 6; i++){
      JointMotor m = new JointMotor();
      m.force = joints[i].motor.force;
      m.freeSpin = joints[i].motor.freeSpin;
      desiredAngle = (i < 3) ? salamander.get_body_setpoint(alpha, i+1, i+9) : 
        salamander.get_body_setpoint(alpha, i+2, i+10);
      desiredAngle *= Mathf.Rad2Deg;
      m.targetVelocity = (desiredAngle - joints[i].angle) / stepTime;
      joints[i].motor = m;
      alpha += 0.5f/6.0f;
    }   
    // Limb joints
    for(int i = 6; i < 10; i++){
      JointMotor m = new JointMotor();
      m.force = joints[i].motor.force;
      m.freeSpin = joints[i].motor.freeSpin;      
      desiredAngle = salamander.get_limb_setpoint(i+10) * Mathf.Rad2Deg;
      m.targetVelocity = (desiredAngle - joints[i].angle) / stepTime;
      joints[i].motor = m;
    }
  }

  void getParams(int n, out float[] a, out float[] theta, out float[] ampl, 
                 out float[] ampl_dot, out int[] osc_class, out float[,] w, 
                 out float[,] phi, out float[] gsl, out float[] gsh, 
                 out float[] gb1, out float[] gb2){
    
    a = new float[n]; 
    theta = new float[n]; 
    ampl = new float[n]; 
    ampl_dot = new float[n];
    osc_class = new int[n];
    w = new float[n,n]; 
    phi = new float[n,n];
    gsl = new float[n];
    gsh = new float[n];
    gb1 = new float[n];
    gb2 = new float[n];
    // Set up intrinsic value: osc_class
    for(int i = 0; i < 16; i ++){
      osc_class[i] = 0;
    }
    for(int i = 16; i < 20; i++){
      osc_class[i] = 1;
    }
    
    // Read in gen values: a, theta, ampl, ampl_dot, w, phi, G
  }
}
