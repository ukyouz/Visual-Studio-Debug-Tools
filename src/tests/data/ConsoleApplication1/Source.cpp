#include <stdio.h>
//#include <string.h>

#define MAX_LEN 255
#define MIN(a, b)   ((a) < (b) ? (a) : (b))

typedef char WCHAR;
typedef long DWORD;

struct TextHolder {
	WCHAR szBuffer[MAX_LEN];
	DWORD dwLen;
} g_Message;

struct A {
	struct {
		int rsv0 : 1;
		int isA : 1;
		int isB : 2;
		int rsv1 : 4;
	} attr;
	DWORD arr[5][6];
	int * pint;
	void (*afunc)(int a, void * b);
	struct TextHolder s;
	const void *x;
};

typedef struct A ADef;

struct B {
	char x;
	struct {
		int rsv0 : 1;
		int isA : 1;
		int isB : 2;
		int rsv1 : 4;
	};

	struct {
		int rsv0 : 1;
		int isA : 1;
		int isB : 2;
		int rsv1 : 4;
	} xxx;
	
	struct TextHolder * s;

	volatile DWORD(*method)(int);
};
typedef struct B BDef, *BDefPtr;


DWORD store_message(TextHolder* pBuf, void * szMessage)
{
	//memcpy(pBuf->szBuffer, szMessage, MAX_LEN);
	return (pBuf->dwLen = MAX_LEN);
}

static volatile DWORD store_message2(int a)
{
	//memcpy(pBuf->szBuffer, szMessage, MAX_LEN);
	return a;
}

ADef gA = {0};
struct B gB = {0};
BDefPtr pB = NULL;

int main()
{
	ADef a = A();
	BDef b = B();
	pB = &b;
	b.rsv0 = 0;
	a.attr.isA = MIN(1, b.rsv0);

	gA.attr.isB = 0;
	b.method = store_message2;
	gB.xxx.isB = b.method(1);

	printf("Hi\n");
	return 0;
}