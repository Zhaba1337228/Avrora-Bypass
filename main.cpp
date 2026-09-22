#include <iostream>

double func_1(double par1)
{
	return (par1 - 32) * (5.0 / 9.0);
}

double func_2(double temperatures[], int size)
{
	double temp = 0.0;
	for (int i = 0; i < size; i++)
	{
		temp += temperatures[i];
	}
	return temp / size;
}

int main()
{
	int n;
	std::cin >> n;

	if (n < 7 || n > 30)
	{
		std::cout << "n is wrong";
		return 1;
	}

	double array[30];

	for (int i = 0; i < n; i++)
	{
		int par1;
		std::cin >> par1;
		array[i] = func_1(par1);
	}

	double averageTemp = func_2(array, n);

	std::cout << "Temperature data: ";
	for (int i = 0; i < n; i++)
	{
		std::cout << array[i];
		if (i < n - 1)
		{
			std::cout << " ";
		}
	}
	std::cout << std::endl;

	std::cout << "Average temperature: " << averageTemp << std::endl;

	return 0;
}
