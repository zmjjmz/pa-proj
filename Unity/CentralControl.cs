using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class CentralControl : MonoBehaviour {
  public class CPG{
    // All angular values are in radians
    private int n;
    private float[] a, theta, ampl, ampl_dot, signal;
    // 0 for body, 1 for limb
    private int[] osc_class;
    private float[,] w, phi;
     
    // Parameters defined by table S1 (body, limb)
    private float[] cv0;
    private float[] cv1;
    private float[] cR0;
    private float[] cR1;
    // ( (dbody_low, dbody_high), (dlimb_low, dlimb_high) )
    private int[,] d_params;

    public CPG(int n, float[] a, float[] theta, float[] ampl, float[] ampl_dot, 
               int[] osc_class, float[,] w, float[,] phi){
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
    // Some segments have only one joint
    joints[0] = GameObject.Find("2").GetComponent<HingeJoint>();
    joints[1] = GameObject.Find("3").GetComponent<HingeJoint>();
    joints[3] = GameObject.Find("5").GetComponent<HingeJoint>();
    joints[4] = GameObject.Find("6").GetComponent<HingeJoint>();
    joints[5] = GameObject.Find("7").GetComponent<HingeJoint>();

    // Others have more than one joint, and these must be differentiated
    HingeJoint[] feet = GameObject.Find("1/Center").GetComponents<HingeJoint>();
    foreach(HingeJoint foot in feet){
      if(foot.connectedBody == GameObject.Find("1/LeftFoot").GetComponent<Rigidbody>()){
        joints[6] = foot;
      }
      else{ 
        joints[7] = foot;
      }
    }
    feet = GameObject.Find("4/Center").GetComponents<HingeJoint>();
    foreach(HingeJoint foot in feet){
      if(foot.connectedBody == GameObject.Find("4/LeftFoot").GetComponent<Rigidbody>()){
        joints[8] = foot;
      }
      else if(foot.connectedBody == GameObject.Find("4/RightFoot").GetComponent<Rigidbody>()){
        joints[9] = foot;
      }
      // Also have to check for segment in front of this segment 
      else{
        joints[2] = foot;
      }
    }
  }

  // This function is called every .2 seconds of simulation, and is where motor changes will happen
  void FixedUpdate(){
    float time = Time.fixedTime;
    foreach (HingeJoint joint in joints) {
      JointMotor m = new JointMotor();
      m.force = joint.motor.force;
      m.freeSpin = joint.motor.freeSpin;
      if(joint.connectedBody.gameObject.name == "LeftFoot" || joint.connectedBody.gameObject.name == "RightFoot"){
        m.targetVelocity = rand.Next(-250, 251);
      }
      else{
        m.targetVelocity = rand.Next(-40, 41);
      }
      joint.motor = m;
    }
  }
}
