#define sensor A0
void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(sensor, INPUT);
}

void loop() {
  if (Serial.available()>0)
    {
       String s = Serial.readStringUntil('\n');   // Until CR (Carriage Return)
       if(s.startsWith("rea"))
       {
        Serial.println(read_ACS());
       }
       
    }
}
float read_ACS()
{
  int total = 0; 
  for(int i = 0; i < 10; i++)
  {
    total+= readAnalog();
    delay(5);
  }
  return (total/10);
}
int readAnalog()
{
  analogRead(sensor);
  delay(5 );
  return analogRead(sensor);
}
