int f1(int a,int b){
  int c;
  c = c + a;
  c = c + b;
  if (c>b) {
    c=a;
  } 
  else {
    c=b;
  }

  return c;
}

int main(){
  int a;
  a = 1;
  int b;
  b = 2;
  b = f1(a, b);

  for(int i=0;i<10;i=i+1) {
    b = i + 1;
  }

  return 0;
}
