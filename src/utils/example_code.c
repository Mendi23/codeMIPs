

int func2(){
    return 1;
}


int func1() {
    return func2();
}

int main () {
    return func1();
}