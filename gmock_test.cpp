#ifndef INC_TEST_GMOCK_REGEX_H
#define INC_TEST_GMOCK_REGEX_H

/// Simple test class to run against the regex in the documentation.
class Test
{
public:
    virtual int simple_method();
    virtual int simple_method_args(int, int);
    virtual int simple_const_method_args(int, int) const;
    virtual int simple_const_method_vals(int x, int y) const;
    virtual std::pair<bool, int> get_pair();
    virtual bool check_map(std::map<int, double>, bool);
    virtual bool transform(Gadget * g) = 0;
    virtual Bar & GetBar();
    virtual const Bar & GetBar() const;
};

#endif
